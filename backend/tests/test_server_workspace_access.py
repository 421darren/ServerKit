"""A developer outside a server's workspace must not operate it over REST —
the same rule the Socket.IO server rooms and terminal already enforce."""
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
def setup(app):
    from app import db
    from app.models.server import Server
    from app.services.workspace_service import WorkspaceService
    admin = _mk_user(db, 'swa_admin', 'admin')
    member = _mk_user(db, 'swa_member', 'developer')
    outsider = _mk_user(db, 'swa_outsider', 'developer')
    ws = WorkspaceService.create_workspace({'name': 'SWA'}, admin.id)
    WorkspaceService.add_member(ws.id, member.id)
    mine = WorkspaceService.create_workspace({'name': 'SWA-out'}, outsider.id)
    server = Server(name='swa-box', workspace_id=ws.id)
    db.session.add(server)
    db.session.commit()
    return {'server': server.id, 'member': member.id, 'outsider': outsider.id,
            'admin': admin.id, 'own_ws': mine.id}


_ROUTES = [
    ('post', '/api/v1/servers/{sid}/terminal', {}),
    ('post', '/api/v1/servers/{sid}/regenerate-token', {}),
    ('put', '/api/v1/servers/{sid}/workspace', {'workspace_id': '{own_ws}'}),
]


@pytest.mark.parametrize('method,url,body', _ROUTES)
def test_outsider_is_refused(client, setup, method, url, body):
    from app.models.server import Server
    body = {k: setup['own_ws'] if v == '{own_ws}' else v for k, v in body.items()}
    before = Server.query.get(setup['server'])
    token_hash, ws_id = before.registration_token_hash, before.workspace_id
    with patch('app.api.servers.TerminalService.create_session',
               return_value={'success': True}) as create:
        resp = getattr(client, method)(url.format(sid=setup['server']), json=body,
                                       headers=_token(setup['outsider']))
    assert resp.status_code == 404
    create.assert_not_called()
    after = Server.query.get(setup['server'])
    assert after.registration_token_hash == token_hash
    assert after.workspace_id == ws_id


@pytest.mark.parametrize('who', ['member', 'admin'])
def test_member_and_admin_can_open_terminal(client, setup, who):
    with patch('app.api.servers.TerminalService.create_session',
               return_value={'success': True, 'session_id': 's1'}) as create:
        resp = client.post(f"/api/v1/servers/{setup['server']}/terminal", json={},
                           headers=_token(setup[who]))
    assert resp.status_code == 200
    create.assert_called_once()


def test_member_can_regenerate_token(client, setup):
    resp = client.post(f"/api/v1/servers/{setup['server']}/regenerate-token",
                       json={}, headers=_token(setup['member']))
    assert resp.status_code == 200
    assert resp.get_json()['registration_token']


def test_default_workspace_servers_stay_shared(client, setup):
    """Servers created without a context land in the Default workspace, which
    nobody joins — developers keep operating them."""
    from app import db
    from app.models.server import Server
    from app.services.workspace_service import WorkspaceService
    server = Server(name='swa-default',
                    workspace_id=WorkspaceService.ensure_default_workspace().id)
    db.session.add(server)
    db.session.commit()
    with patch('app.api.servers.TerminalService.create_session',
               return_value={'success': True, 'session_id': 's2'}):
        resp = client.post(f'/api/v1/servers/{server.id}/terminal', json={},
                           headers=_token(setup['outsider']))
    assert resp.status_code == 200
