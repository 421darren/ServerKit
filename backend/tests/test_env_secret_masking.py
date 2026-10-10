"""A read-only (viewer) grant on an app must never see secret env values —
masking used to be opt-in from the client via ?mask=true."""
import pytest

SECRET = 's3cr3t-db-password'


def _mk_user(db, username, role):
    from app.models import User
    from werkzeug.security import generate_password_hash
    u = User(email=f'{username}@t.local', username=username,
             password_hash=generate_password_hash('x'), role=role, is_active=True)
    db.session.add(u)
    db.session.commit()
    return u


def _token(user_id):
    from flask_jwt_extended import create_access_token
    return {'Authorization': f'Bearer {create_access_token(identity=user_id)}'}


@pytest.fixture
def shared_app(app):
    from app import db
    from app.models import Application
    from app.services.env_service import EnvService
    from app.services.resource_grant_service import ResourceGrantService
    owner = _mk_user(db, 'esm_owner', 'developer')
    viewer = _mk_user(db, 'esm_viewer', 'developer')
    editor = _mk_user(db, 'esm_editor', 'developer')
    application = Application(name='esm-app', app_type='docker', user_id=owner.id)
    db.session.add(application)
    db.session.commit()
    ResourceGrantService.grant(viewer.id, 'application', application.id, role='viewer')
    ResourceGrantService.grant(editor.id, 'application', application.id, role='editor')
    EnvService.set_env_var(application.id, 'DB_PASSWORD', SECRET, is_secret=True)
    EnvService.set_env_var(application.id, 'LOG_LEVEL', 'info')
    return {'id': application.id, 'owner': owner.id, 'viewer': viewer.id, 'editor': editor.id}


def _urls(app_id):
    return [f'/api/v1/apps/{app_id}/env',
            f'/api/v1/apps/{app_id}/env?mask=false',
            f'/api/v1/apps/{app_id}/env/DB_PASSWORD',
            f'/api/v1/apps/{app_id}/env/export?include_secrets=true']


def test_viewer_never_sees_secret_values(client, shared_app):
    for url in _urls(shared_app['id']):
        resp = client.get(url, headers=_token(shared_app['viewer']))
        assert resp.status_code == 200, url
        assert SECRET not in resp.get_data(as_text=True), url


def test_viewer_still_sees_plain_values(client, shared_app):
    resp = client.get(f"/api/v1/apps/{shared_app['id']}/env",
                      headers=_token(shared_app['viewer']))
    values = {v['key']: v['value'] for v in resp.get_json()['env_vars']}
    assert values['LOG_LEVEL'] == 'info'


@pytest.mark.parametrize('who', ['owner', 'editor'])
def test_editors_can_read_secrets(client, shared_app, who):
    resp = client.get(f"/api/v1/apps/{shared_app['id']}/env/DB_PASSWORD",
                      headers=_token(shared_app[who]))
    assert resp.get_json()['env_var']['value'] == SECRET
    resp = client.get(f"/api/v1/apps/{shared_app['id']}/env/export",
                      headers=_token(shared_app[who]))
    assert SECRET in resp.get_json()['content']
