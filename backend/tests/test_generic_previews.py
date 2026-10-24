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
    def build(parent, preview, path, image):
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
    def build(*args):
        original(*args)
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
