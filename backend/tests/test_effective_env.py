"""Effective deploy env: shared variable groups merged under local env vars,
and proof that the docker deploy path injects the merged result."""
import types


def _make_app(workspace_id=None, project_id=None, environment_id=None, port=8080):
    from app import db
    from app.models.application import Application
    a = Application(
        name='svc', app_type='docker', status='running', user_id=1, port=port,
        workspace_id=workspace_id, project_id=project_id, environment_id=environment_id,
    )
    db.session.add(a)
    db.session.commit()
    return a


def _set_local(app_id, key, value, is_secret=False):
    from app import db
    from app.models import EnvironmentVariable
    ev = EnvironmentVariable(application_id=app_id, key=key, is_secret=is_secret)
    ev.value = value  # encrypted via the model's value setter
    db.session.add(ev)
    db.session.commit()
    return ev


def _make_scoped_group(scope_type, scope_id, key, value):
    """A group scoped to a workspace/project/environment auto-applies to apps in
    that scope (no attachment needed)."""
    from app import db
    from app.models.shared_resource import SharedVariableGroup, SharedVariable
    g = SharedVariableGroup(scope_type=scope_type, scope_id=str(scope_id), name=f'{scope_type}-grp')
    db.session.add(g)
    db.session.commit()
    v = SharedVariable(group_id=g.id, key=key, is_secret=False)
    v.value = value
    db.session.add(v)
    db.session.commit()
    return g


def test_local_only_when_no_shared(app):
    from app.services.env_service import EnvService
    with app.app_context():
        a = _make_app(workspace_id=1)
        _set_local(a.id, 'FOO', 'foo')
        _set_local(a.id, 'BAR', 'bar')
        env = EnvService.get_effective_env(a.id)
        assert env == {'FOO': 'foo', 'BAR': 'bar'}


def test_shared_fills_in_missing_keys(app):
    from app.services.env_service import EnvService
    with app.app_context():
        a = _make_app(workspace_id=7)
        _make_scoped_group('workspace', 7, 'SHARED_KEY', 'shared_val')
        _set_local(a.id, 'LOCAL_KEY', 'local_val')
        env = EnvService.get_effective_env(a.id)
        assert env['SHARED_KEY'] == 'shared_val'   # came from the shared group
        assert env['LOCAL_KEY'] == 'local_val'


def test_local_overrides_shared_same_key(app):
    from app.services.env_service import EnvService
    with app.app_context():
        a = _make_app(workspace_id=11)
        _make_scoped_group('workspace', 11, 'DATABASE_URL', 'shared://db')
        _set_local(a.id, 'DATABASE_URL', 'local://db')
        env = EnvService.get_effective_env(a.id)
        # The app's own value wins — matches the "local value applies" UI hint.
        assert env['DATABASE_URL'] == 'local://db'


def test_shared_hierarchy_under_local(app):
    from app.services.env_service import EnvService
    with app.app_context():
        a = _make_app(workspace_id=20, environment_id=30)
        _make_scoped_group('workspace', 20, 'TIER', 'ws')
        _make_scoped_group('environment', 30, 'TIER', 'env')
        # environment scope outranks workspace scope (both below local)
        env = EnvService.get_effective_env(a.id)
        assert env['TIER'] == 'env'
        _set_local(a.id, 'TIER', 'local')
        assert EnvService.get_effective_env(a.id)['TIER'] == 'local'


def test_shared_resolution_failure_is_best_effort(app, monkeypatch):
    from app.services.env_service import EnvService
    from app.services.shared_resource_service import SharedResourceService
    with app.app_context():
        a = _make_app(workspace_id=1)
        _set_local(a.id, 'KEEP', 'me')

        def _boom(*args, **kwargs):
            raise RuntimeError('shared store down')
        monkeypatch.setattr(SharedResourceService, 'resolve_hierarchical', _boom)

        env = EnvService.get_effective_env(a.id)
        assert env == {'KEEP': 'me'}   # deploy never blocked by shared failure


def test_deploy_docker_injects_effective_env(app, monkeypatch):
    """The docker deploy path must hand run_container the merged env (shared
    underneath local), not just local env vars."""
    from app.services import deployment_service as ds_mod
    from app.services.deployment_service import DeploymentService

    with app.app_context():
        a = _make_app(workspace_id=42)
        _make_scoped_group('workspace', 42, 'SHARED_ONLY', 'from_group')
        _make_scoped_group('workspace', 42, 'OVERRIDE_ME', 'group_value')
        _set_local(a.id, 'OVERRIDE_ME', 'local_value')
        _set_local(a.id, 'LOCAL_ONLY', 'local_only')

        captured = {}

        class FakeDocker:
            @staticmethod
            def get_container(name):
                return None

            @staticmethod
            def run_container(**kwargs):
                captured.update(kwargs)
                return {'success': True, 'container_id': 'deadbeef'}

        monkeypatch.setattr(ds_mod, 'DockerService', FakeDocker)

        deployment = types.SimpleNamespace(image_tag='myimg:1.0')
        result = DeploymentService._deploy_docker(a, deployment)
        assert result['success'] is True

        env = captured.get('env') or {}
        assert env['SHARED_ONLY'] == 'from_group'    # shared var reached the container
        assert env['OVERRIDE_ME'] == 'local_value'   # local won the collision
        assert env['LOCAL_ONLY'] == 'local_only'


def test_effective_view_matches_winners_without_values(app):
    from app import db
    from app.services.env_service import EnvService
    with app.app_context():
        a = _make_app(workspace_id=7)
        _make_scoped_group('workspace', 7, 'SHARED', 'inherited-secret')
        _make_scoped_group('workspace', 7, 'OVERRIDE', 'old-secret')
        _set_local(a.id, 'OVERRIDE', 'new-secret', is_secret=True)
        local = _set_local(a.id, 'TARGET', 'target-secret')
        local.target_service = 'web'
        db.session.commit()
        for service in ('web', 'worker'):
            view = EnvService.get_effective_env_view(a.id, service)
            deployed = EnvService.get_effective_env_for_services(a.id, [service])[service]
            assert view['complete'] and view['values_hidden']
            assert {row['key'] for row in view['env_vars']} == set(deployed)
            rows = {row['key']: row for row in view['env_vars']}
            assert rows['SHARED']['source_scope'] == 'workspace'
            assert rows['OVERRIDE']['source_scope'] == 'local'
            assert rows['OVERRIDE']['overrides']['group_name'] == 'workspace-grp'
            assert 'secret' not in str(view).replace('is_secret', '')
            assert all('value' not in row for row in rows.values())


def test_effective_view_reports_incomplete_shared_resolution(app, monkeypatch):
    from app.services.env_service import EnvService
    from app.services.shared_resource_service import SharedResourceService
    with app.app_context():
        a = _make_app()
        _set_local(a.id, 'LOCAL', 'private')
        def fail(*args, **kwargs):
            raise RuntimeError('sensitive connection details')
        monkeypatch.setattr(SharedResourceService, 'resolve_hierarchical', fail)
        view = EnvService.get_effective_env_view(a.id)
        assert view['complete'] is False
        assert [row['key'] for row in view['env_vars']] == ['LOCAL']
        assert 'sensitive' not in str(view)
        assert EnvService.get_effective_env(a.id) == {'LOCAL': 'private'}


def test_effective_view_never_resolves_local_references(app, monkeypatch):
    from app import db
    from app.services.env_service import EnvService
    with app.app_context():
        a = _make_app()
        ev = _set_local(a.id, 'REF', '')
        ev.set_reference({'kind': 'secret', 'secret': 'credential'})
        db.session.commit()
        def fail(*args):
            raise AssertionError('metadata must not decrypt or resolve local values')
        monkeypatch.setattr(EnvService, '_resolve_var_value', fail)
        view = EnvService.get_effective_env_view(a.id)
        assert view['env_vars'][0]['is_reference'] is True
        assert 'credential' not in str(view)
