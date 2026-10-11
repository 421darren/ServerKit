"""Build commands and deploy/template scripts come from repositories and
registries; they must not inherit the panel's own secrets."""
import pytest

from app.utils.system import app_process_env

SECRETS = {
    'SECRET_KEY': 'flask-session-key',
    'JWT_SECRET_KEY': 'jwt-signing-key',
    'DATABASE_URL': 'postgresql://panel:pw@db/serverkit',
    'SERVERKIT_ENCRYPTION_KEY': 'fernet-key',
    'SERVERKIT_GITHUB_TOKEN': 'ghp_x',
    'SOURCE_GITHUB_CLIENT_SECRET': 'oauth-secret',
}


@pytest.fixture
def panel_env(monkeypatch):
    for key, value in SECRETS.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '1700000000')  # a build var, not a secret


def _assert_clean(env):
    leaked = sorted(k for k in SECRETS if k in env)
    assert leaked == [], f'panel secrets reached the script: {leaked}'
    assert 'PATH' in env


def test_helper_drops_panel_secrets_and_keeps_the_rest(panel_env):
    env = app_process_env({'NODE_ENV': 'production'})
    _assert_clean(env)
    assert env['SOURCE_DATE_EPOCH'] == '1700000000'
    assert env['NODE_ENV'] == 'production'


def test_extra_vars_are_the_apps_to_set(panel_env):
    # An app may define its own DATABASE_URL; that is its value, not ours.
    assert app_process_env({'DATABASE_URL': 'mysql://app'})['DATABASE_URL'] == 'mysql://app'


def _capture_run_checked(monkeypatch, module):
    seen = {}

    def fake(cmd, **kwargs):
        seen['env'] = kwargs.get('env')
        return {'success': True, 'output': '', 'stderr': '', 'error': None, 'returncode': 0}
    monkeypatch.setattr(f'{module}.run_checked', fake)
    return seen


def test_template_scripts(panel_env, monkeypatch, tmp_path):
    from app.services.template_service import TemplateService
    seen = _capture_run_checked(monkeypatch, 'app.services.template_service')
    TemplateService._run_script('echo hi', str(tmp_path), {'APP_PORT': '8080'})
    _assert_clean(seen['env'])
    assert seen['env']['APP_PORT'] == '8080'


def test_git_deploy_scripts(panel_env, monkeypatch, tmp_path):
    from app.services.git_deploy_service import GitDeployService
    seen = _capture_run_checked(monkeypatch, 'app.services.git_deploy_service')
    GitDeployService._run_script('echo hi', str(tmp_path))
    _assert_clean(seen['env'])
    assert seen['env']['DEPLOY_DIR'] == str(tmp_path)


def test_python_app_commands(panel_env, monkeypatch, tmp_path):
    from app.services.python_service import PythonService
    (tmp_path / 'venv' / 'bin').mkdir(parents=True)
    (tmp_path / 'venv' / 'bin' / 'python').write_text('')
    monkeypatch.setattr(PythonService, 'get_env_vars', staticmethod(lambda path: {}))
    seen = _capture_run_checked(monkeypatch, 'app.services.python_service')
    PythonService.run_command(str(tmp_path), 'manage.py migrate')
    _assert_clean(seen['env'])


def test_custom_build_commands(panel_env, fake_subprocess, tmp_path):
    from subprocess_stub import FakeProc
    from app.services.build_service import BuildService
    seen = {}

    def bash(argv, kwargs):
        seen['env'] = kwargs['env']
        return FakeProc(returncode=0, args=argv)
    fake_subprocess.when(['bash'], bash)
    BuildService.build_with_custom_command(
        1, str(tmp_path), 'npm run build', env_vars={'NODE_ENV': 'production'})
    _assert_clean(seen['env'])
    assert seen['env']['NODE_ENV'] == 'production'
