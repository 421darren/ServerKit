"""Generic previews: real orchestration with fake external Git/Docker/nginx effects."""
import json
from types import SimpleNamespace
import pytest
from app import db
from app.models.application_preview import ApplicationPreview
from app.services.preview_service import PreviewService
from app.services.previews import runtime, source
from app.services.previews.plan import PreviewError, identity, workspace, validate
from test_previews import _mk_app

SHA = 'a' * 40
PR = {'pr_number': 7, 'branch': 'feature/preview', 'commit_sha': SHA}


@pytest.fixture
def host(app, monkeypatch, tmp_path):
    from app.services.git_service import GitService
    from app.services.build_service import BuildService
    resources = {'containers': {}, 'images': set(), 'routes': {}, 'calls': []}
    monkeypatch.setattr(runtime, 'ROOT', tmp_path / 'previews')
    monkeypatch.setattr(BuildService, 'BUILD_LOG_DIR', str(tmp_path / 'logs'))
    monkeypatch.setattr(GitService, 'get_app_config', lambda _: {'repo_url': 'https://example.test/repo.git'})
    def prepare(parent, preview, path, url):
        resources['calls'].append(('clone', str(path), url))
        path.mkdir()
        (path / 'Dockerfile').write_text('FROM scratch')
    def build(parent, preview, path, image, **kwargs):
        resources['calls'].append(('build', image))
        resources['images'].add(image)
    monkeypatch.setattr(source, 'prepare', prepare)
    monkeypatch.setattr(source, 'build', build)
    def run_container(**kwargs):
        resources['calls'].append(('run', kwargs))
        name = kwargs['name']
        resources['containers'][name] = {'Id': name + '-id',
            'Config': {'Labels': kwargs['labels']}, 'State': {'Running': True},
            'NetworkSettings': {'Ports': {'8400/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '39001'}]}}}
        return {'success': True, 'container_id': name + '-id'}
    def inspect(args, **kwargs):
        kind, _, name = args
        data = resources['containers'].get(name) if kind == 'container' else ({} if name in resources['images'] else None)
        if data is None:
            return {'success': False, 'error': 'No such object'}
        return {'success': True, 'output': json.dumps([data])}
    def remove(name, **kwargs):
        resources['calls'].append(('remove', name, kwargs))
        resources['containers'].pop(name, None)
        return {'success': True}
    def remove_image(name, **kwargs):
        resources['images'].discard(name)
        return {'success': True}
    def publish(name, kind, domains, **kwargs):
        resources['routes'][name] = domains
        return {'success': True}
    def delete(name):
        resources['routes'].pop(name, None)
        return {'success': True}
    monkeypatch.setattr(runtime.DockerService, 'run_container', run_container)
    monkeypatch.setattr(runtime.DockerService, 'run', inspect)
    monkeypatch.setattr(runtime.DockerService, 'remove_container', remove)
    monkeypatch.setattr(runtime.DockerService, 'remove_image', remove_image)
    monkeypatch.setattr(runtime.NginxService, 'list_sites', lambda: [])
    monkeypatch.setattr(runtime.NginxService, 'create_site', publish)
    monkeypatch.setattr(runtime.NginxService, 'disable_site', lambda _: {'success': True})
    monkeypatch.setattr(runtime.NginxService, 'delete_site', delete)
    monkeypatch.setattr(runtime.SiteDomainService, 'covering_base', lambda _: None)
    monkeypatch.setattr(runtime.health_gate, 'gate_for_app', lambda *a, **kw: {'status': 200})
    with app.app_context():
        parent = _mk_app(name='generic')
        parent.container_id = 'production-container'
        parent.docker_image = 'production:live'
        db.session.commit()
        PreviewService.enable_previews(parent.id, {'enabled': True, 'domain_template': 'pr-{pr_number}.test.example'})
        yield parent, resources


def test_create_redeploy_destroy_are_isolated_and_idempotent(host):
    parent, resources = host
    first = PreviewService.create_preview(parent, PR)
    assert first['status'] == 'running', first
    assert first['url'] == 'http://pr-7.test.example'
    old_ids = first['container_ids']
    call = next(c[1] for c in resources['calls'] if c[0] == 'run')
    assert call['ports'] == ['127.0.0.1::8400']
    assert 'volumes' not in call and 'network' not in call
    assert call['env'] == {'SERVERKIT_PREVIEW': 'true', 'SERVERKIT_PR_NUMBER': '7', 'SERVERKIT_PREVIEW_BRANCH': 'feature/preview'}
    second = PreviewService.create_preview(parent, {**PR, 'commit_sha': 'b' * 40})
    assert second['status'] == 'running'
    assert second['id'] == first['id'] and second['container_ids'] != old_ids
    assert len(resources['containers']) == len(resources['images']) == len(resources['routes']) == 1
    result = PreviewService.destroy_preview(first['id'])
    assert result['status'] == 'destroyed'
    assert not resources['containers'] and not resources['images'] and not resources['routes']
    assert not list(runtime.ROOT.iterdir())
    assert PreviewService.destroy_preview(first['id'])['status'] == 'destroyed'
    db.session.refresh(parent)
    assert parent.container_id == 'production-container'
    assert parent.docker_image == 'production:live' and parent.port == 8400


@pytest.mark.parametrize('failure', ['clone', 'build', 'start', 'health', 'route'])
def test_each_failure_compensates_owned_resources(host, monkeypatch, failure):
    parent, resources = host
    def fail(*args, **kwargs):
        raise RuntimeError('secret-diagnostic-do-not-expose')
    owner, attr = {'clone': (source, 'prepare'), 'build': (source, 'build'),
                   'start': (runtime, 'start'), 'health': (runtime.health_gate, 'gate_for_app'),
                   'route': (runtime, 'publish')}[failure]
    monkeypatch.setattr(owner, attr, fail)
    result = PreviewService.create_preview(parent, PR)
    assert result['status'] == 'failed' and result['url'] is None
    assert 'secret-diagnostic' not in str(result)
    assert not resources['containers'] and not resources['images'] and not resources['routes']
    row = db.session.get(ApplicationPreview, result['id'])
    assert row.get_runtime_state() == {}


def test_cleanup_failure_preserves_journal_and_retry_succeeds(host, monkeypatch):
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    remove = runtime.DockerService.remove_container
    monkeypatch.setattr(runtime.DockerService, 'remove_container', lambda *a, **kw: {'success': False})
    failed = PreviewService.destroy_preview(result['id'])
    assert failed.get('error')
    row = db.session.get(ApplicationPreview, result['id'])
    assert row.status == 'failed' and row.deleted_at is None
    assert row.get_runtime_state()['container'] is True
    assert resources['containers']
    monkeypatch.setattr(runtime.DockerService, 'remove_container', remove)
    assert PreviewService.destroy_preview(result['id'])['status'] == 'destroyed'
    assert not resources['containers']


def test_domain_conflict_prevents_host_effects(host):
    from app.models import Domain
    parent, resources = host
    db.session.add(Domain(name='pr-7.test.example', application_id=parent.id))
    db.session.commit()
    result = PreviewService.create_preview(parent, PR)
    assert result['status'] == 'failed'
    assert not resources['calls']


def test_unsupported_target_and_bad_ref_do_not_provision(host):
    parent, resources = host
    parent.compose_file = 'compose.yml'
    db.session.commit()
    assert PreviewService.create_preview(parent, PR)['status'] == 'failed'
    parent.compose_file = None
    db.session.commit()
    assert PreviewService.create_preview(parent, {**PR, 'commit_sha': '--bad'})['status'] == 'failed'
    assert not resources['calls']


def test_unknown_provider_does_not_destroy_existing_previews(host):
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    assert PreviewService.sync_previews(parent.id).get('error')
    assert db.session.get(ApplicationPreview, result['id']).status == 'running'
    assert resources['containers']


def test_cleanup_rejects_missing_ownership(host):
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    next(iter(resources['containers'].values()))['Config']['Labels'] = {}
    assert PreviewService.destroy_preview(result['id']).get('error')
    assert resources['containers']


def test_close_supersedes_queued_create_before_row_has_runtime(host, monkeypatch):
    from app.services.previews.requests import enqueue
    from app.jobs.service import JobService
    parent, resources = host
    jobs = []
    def capture(kind, payload, **kwargs):
        job = SimpleNamespace(kind=kind, get_payload=lambda: payload)
        jobs.append(job)
        return job
    monkeypatch.setattr(JobService, 'enqueue', capture)
    enqueue(parent.id, PR)
    enqueue(parent.id, PR, action='destroy')
    assert PreviewService._job_create(jobs[0])['reason'] == 'superseded'
    assert PreviewService._job_destroy(jobs[1])['status'] == 'destroyed'
    assert not resources['calls']


def test_close_during_build_cleans_up_without_publishing(host, monkeypatch):
    from app.services.previews.requests import enqueue
    from app.jobs.service import JobService
    parent, resources = host
    monkeypatch.setattr(JobService, 'enqueue', lambda *a, **kw: None)
    original = source.build
    def build(*args, **kwargs):
        original(*args, **kwargs)
        enqueue(parent.id, PR, action='destroy')
    monkeypatch.setattr(source, 'build', build)
    result = PreviewService.create_preview(parent, PR)
    assert result['status'] == 'failed'
    assert not resources['routes'] and not resources['containers']


def test_cleanup_paths_cannot_escape(tmp_path):
    with pytest.raises(PreviewError):
        workspace(tmp_path, 1, '../escape')
    with pytest.raises(PreviewError):
        identity(-1, 'a' * 32)


def test_failed_cleanup_blocks_purge_and_retention_sweep(host, monkeypatch):
    from datetime import datetime, timedelta
    from app.services import recycle_bin_service
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    parent.deleted_at = datetime.utcnow() - timedelta(days=90)
    db.session.commit()
    monkeypatch.setattr(runtime.DockerService, 'remove_container', lambda *a, **kw: {'success': False})
    ok, reason = recycle_bin_service.purge('application', parent.id)
    assert not ok and 'Preview cleanup' in reason
    assert db.session.get(ApplicationPreview, result['id']).get_runtime_state()
    counts = recycle_bin_service.purge_expired()
    assert counts.get('application', 0) == 0
    assert resources['containers']


def test_environment_inheritance_is_opt_in(host):
    from app.services.env_service import EnvService
    parent, resources = host
    EnvService.set_env_var(parent.id, 'DATABASE_URL', 'production-credential', is_secret=True)
    PreviewService.create_preview(parent, PR)
    run = [call[1] for call in resources['calls'] if call[0] == 'run'][-1]
    assert 'DATABASE_URL' not in run['env']
    PreviewService.enable_previews(parent.id, {'inherit_environment': True})
    PreviewService.create_preview(parent, PR)
    run = [call[1] for call in resources['calls'] if call[0] == 'run'][-1]
    assert run['env']['DATABASE_URL'] == 'production-credential'


def test_nginx_reload_failure_keeps_runtime_and_failed_status(host, monkeypatch):
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    monkeypatch.setattr(runtime.NginxService, 'disable_site', lambda _: {'success': False})
    assert PreviewService.destroy_preview(result['id']).get('error')
    row = db.session.get(ApplicationPreview, result['id'])
    assert row.get_runtime_state()['vhost']
    assert row.deleted_at is None and resources['containers']


def test_container_daemon_outage_is_not_treated_as_already_removed(host, monkeypatch):
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    monkeypatch.setattr(runtime.DockerService, 'run', lambda *a, **kw: {'success': False, 'error': 'daemon unavailable'})
    assert PreviewService.destroy_preview(result['id']).get('error')
    assert db.session.get(ApplicationPreview, result['id']).get_runtime_state()['container']


def test_api_queues_without_building_and_requires_app_write(host, client, monkeypatch):
    from factories import headers_for, make_user
    from app.models import User
    from app.jobs.service import JobService
    parent, resources = host
    owner = db.session.get(User, parent.user_id)
    queued = []
    monkeypatch.setattr(JobService, 'enqueue', lambda *a, **kw: queued.append((a, kw)) or SimpleNamespace(id='job-id'))
    url = f'/api/v1/apps/{parent.id}/previews'
    result = client.post(url, headers=headers_for(owner), json=PR)
    assert result.status_code == 202 and result.json['job_id'] == 'job-id'
    assert not resources['calls'] and len(queued) == 1
    assert client.post(url, headers=headers_for(owner), json={**PR, 'commit_sha': '-bad'}).status_code == 400
    stranger = make_user(db, role='developer')
    assert client.post(url, headers=headers_for(stranger), json=PR).status_code in (403, 404)
    viewer = make_user(db, role='viewer')
    assert client.post(url, headers=headers_for(viewer), json=PR).status_code == 403
    assert len(queued) == 1


def test_source_checkout_is_pinned_and_removes_git_credentials(tmp_path, monkeypatch):
    calls = []
    target = tmp_path / 'checkout'
    def clone(path, url, branch):
        (target / '.git').mkdir(parents=True)
        (target / '.git' / 'config').write_text('credential')
        calls.append(('clone', path, url, branch))
        return {'success': True}
    monkeypatch.setattr(source.GitService, 'clone_repository', clone)
    monkeypatch.setattr(source, 'run_checked', lambda argv, **kw: calls.append(argv) or {'success': True})
    source.prepare(None, SimpleNamespace(**PR), target, 'https://example.test/repo.git')
    assert any('--is-ancestor' in call and SHA in call for call in calls)
    assert any('--detach' in call and SHA in call for call in calls)
    assert not (target / '.git').exists()


def test_build_uses_isolated_namespace_and_existing_dispatcher(tmp_path, monkeypatch):
    from app.services.build_service import BuildService
    calls = []
    config = {'app_path': '/production', 'build_method': 'dockerfile',
              'env_vars': {'SECRET': 'private'}, 'build_args': {'TOKEN': 'private'}}
    monkeypatch.setattr(BuildService, 'get_app_build_config', lambda _: config)
    monkeypatch.setattr(BuildService, 'build_from_config', lambda *a, **kw: calls.append((a, kw)) or {'success': True})
    source.build(SimpleNamespace(id=1), SimpleNamespace(id=2), tmp_path, 'isolated:tag')
    args, kwargs = calls[0]
    assert args[0] == 'preview-2'
    assert args[1]['app_path'] == str(tmp_path)
    assert args[1]['env_vars'] == args[1]['build_args'] == {}
    assert config['app_path'] == '/production' and config['env_vars']['SECRET'] == 'private'
    assert kwargs['image_tag'] == 'isolated:tag'


def test_preview_migration_round_trip_and_existing_schema():
    import importlib.util
    from pathlib import Path
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    file = Path(__file__).parents[1] / 'migrations/versions/111_preview_runtime.py'
    spec = importlib.util.spec_from_file_location('preview_migration', file)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine('sqlite://')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE application_previews (id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('CREATE TABLE application_preview_settings (application_id INTEGER PRIMARY KEY)')
        connection.exec_driver_sql('INSERT INTO application_preview_settings VALUES (1)')
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            migration.upgrade()
            assert connection.exec_driver_sql('SELECT inherit_environment FROM application_preview_settings').scalar() == 0
            assert 'runtime_state' in {c['name'] for c in sa.inspect(connection).get_columns('application_previews')}
            migration.downgrade()
            assert {c['name'] for c in sa.inspect(connection).get_columns('application_previews')} == {'id'}


def test_partial_docker_run_is_compensated(host, monkeypatch):
    parent, resources = host
    original = runtime.DockerService.run_container
    def partial(**kwargs):
        original(**kwargs)
        return {'success': False, 'error': 'start failed after create'}
    monkeypatch.setattr(runtime.DockerService, 'run_container', partial)
    result = PreviewService.create_preview(parent, PR)
    assert result['status'] == 'failed'
    assert not resources['containers'] and not resources['images']


def test_partial_nginx_publish_is_compensated(host, monkeypatch):
    parent, resources = host
    original = runtime.NginxService.create_site
    def partial(*args, **kwargs):
        original(*args, **kwargs)
        return {'success': False}
    monkeypatch.setattr(runtime.NginxService, 'create_site', partial)
    result = PreviewService.create_preview(parent, PR)
    assert result['status'] == 'failed'
    assert not resources['routes'] and not resources['containers']


def test_purge_cleans_preview_before_deleting_ownership_record(host, monkeypatch):
    from datetime import datetime
    from app.services import recycle_bin_service
    parent, resources = host
    result = PreviewService.create_preview(parent, PR)
    parent.deleted_at = datetime.utcnow()
    db.session.commit()
    # Parent host lifecycle has its own suite; only previews touch Docker here.
    monkeypatch.setattr(recycle_bin_service, '_run_purge_hook', lambda *a: None)
    ok, warning = recycle_bin_service.purge('application', parent.id)
    assert ok, warning
    assert not resources['containers'] and not resources['images']
    assert db.session.get(ApplicationPreview, result['id']) is None


def test_preview_uses_slot_container_port_without_mutating_production_slot(host):
    from app.models.app_slot import AppSlot
    parent, resources = host
    parent.active_slot = 'a'
    parent.slot_deploys_enabled = True
    parent.port = 39005  # live host binding, not the image's listening port
    slot = AppSlot(application_id=parent.id, slot='a', container_port=8400,
                   host_port=39005, container_name='production-slot', state='live')
    db.session.add(slot)
    db.session.commit()
    assert PreviewService.create_preview(parent, PR)['status'] == 'running'
    run = next(call[1] for call in resources['calls'] if call[0] == 'run')
    assert run['ports'] == ['127.0.0.1::8400']
    db.session.refresh(slot)
    assert slot.host_port == 39005 and slot.container_name == 'production-slot'
