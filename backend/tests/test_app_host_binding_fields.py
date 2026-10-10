"""Non-admins must not point an app at host paths/units, and an app name must
stay a plain slug: root-run code turns these into compose invocations, nginx
site files and `rm -f` targets."""
from unittest.mock import patch

import pytest


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
def users(app):
    from app import db
    return {'dev': _mk_user(db, 'hb_dev', 'developer').id,
            'admin': _mk_user(db, 'hb_admin', 'admin').id}


@pytest.mark.parametrize('field,value', [
    ('root_path', '/'),
    ('compose_file', '../../etc/evil.yml'),
    ('systemd_unit', 'ssh.service'),
    ('managed_by', 'systemd'),
])
def test_developer_cannot_create_with_host_fields(client, users, field, value):
    from app.models import Application
    resp = client.post('/api/v1/apps', headers=_token(users['dev']),
                       json={'name': f'hb-{field}', 'app_type': 'docker', field: value})
    assert resp.status_code == 403
    assert Application.query.filter_by(name=f'hb-{field}').first() is None


def test_create_slugs_the_name(client, users):
    resp = client.post('/api/v1/apps', headers=_token(users['dev']),
                       json={'name': 'My App; }\nserver {', 'app_type': 'php'})
    assert resp.status_code == 201
    assert resp.get_json()['app']['name'] == 'my-app-server'


def test_create_refuses_a_taken_name(client, users):
    body = {'name': 'hb-taken', 'app_type': 'php'}
    assert client.post('/api/v1/apps', headers=_token(users['dev']), json=body).status_code == 201
    assert client.post('/api/v1/apps', headers=_token(users['dev']), json=body).status_code == 400


@pytest.fixture
def dev_app(client, users):
    resp = client.post('/api/v1/apps', headers=_token(users['dev']),
                       json={'name': 'hb-own', 'app_type': 'docker'})
    return resp.get_json()['app']['id']


def test_owner_cannot_repoint_host_fields(client, users, dev_app):
    from app.models import Application
    resp = client.put(f'/api/v1/apps/{dev_app}', headers=_token(users['dev']),
                      json={'root_path': '/', 'compose_file': 'x.yml'})
    assert resp.status_code == 403
    app = Application.query.get(dev_app)
    assert app.root_path is None and app.compose_file is None


def test_admin_can_set_host_fields(client, users, dev_app):
    resp = client.put(f'/api/v1/apps/{dev_app}', headers=_token(users['admin']),
                      json={'root_path': '/srv/hb-own'})
    assert resp.status_code == 200
    assert resp.get_json()['app']['root_path'] == '/srv/hb-own'


@pytest.mark.parametrize('name', ['../../etc/passwd', 'Has Space', 'x;y', ''])
def test_rename_must_be_a_slug(client, users, dev_app, name):
    resp = client.put(f'/api/v1/apps/{dev_app}', headers=_token(users['dev']),
                      json={'name': name})
    assert resp.status_code == 400


def test_owner_can_still_update_safe_fields(client, users, dev_app):
    resp = client.put(f'/api/v1/apps/{dev_app}', headers=_token(users['dev']),
                      json={'name': 'hb-renamed', 'port': 8123})
    assert resp.status_code == 200
    assert resp.get_json()['app']['name'] == 'hb-renamed'


@pytest.mark.parametrize('method', ['enable_site', 'disable_site', 'delete_site'])
@pytest.mark.parametrize('name', ['../../etc/passwd', 'a/b', '..', ''])
def test_nginx_site_methods_refuse_paths(method, name):
    from app.services.nginx_service import NginxService
    with patch('app.services.nginx_service.run_privileged') as run:
        result = getattr(NginxService, method)(name)
    assert result['success'] is False
    assert 'Invalid site name' in result['error']
    run.assert_not_called()
