"""
A server without a docker-mailserver container must get a clear
"not installed" answer (code + 404), not a raw Docker error and a 500.
"""
import pytest

from app.services import mail_server_service as mss
from app.services.mail_server_service import MailServerService

DOCKER_ERR = 'exec: Error response from daemon: No such container: mailserver'


def _fake(monkeypatch, result):
    monkeypatch.setattr(mss.RemoteDockerService, 'exec_command',
                        staticmethod(lambda **kw: result))


@pytest.mark.parametrize('fn', ['list_mailboxes', 'list_aliases'])
@pytest.mark.parametrize('result', [
    {'success': False, 'error': DOCKER_ERR},
    {'success': True, 'data': {'stdout': '', 'stderr': DOCKER_ERR, 'exit_code': 1}},
])
def test_missing_container_is_reported_as_not_installed(monkeypatch, fn, result):
    _fake(monkeypatch, result)
    r = getattr(MailServerService, fn)(server_id='srv')
    assert r == {
        'success': False,
        'code': 'MAIL_SERVER_NOT_INSTALLED',
        'error': 'No mail server is installed on this server.',
    }


def test_other_errors_are_not_masked(monkeypatch):
    _fake(monkeypatch, {'success': False, 'error': 'agent offline', 'code': 'AGENT_OFFLINE'})
    r = MailServerService.list_mailboxes(server_id='srv')
    assert r['code'] == 'AGENT_OFFLINE'


def test_route_returns_404_for_not_installed(app, monkeypatch):
    import app.api.servers_remote as servers_api
    monkeypatch.setattr(servers_api.MailServerService, 'list_mailboxes',
                        staticmethod(lambda **kw: {
                            'success': False,
                            'code': 'MAIL_SERVER_NOT_INSTALLED',
                            'error': 'No mail server is installed on this server.'}))
    view = servers_api.list_server_mailboxes
    while hasattr(view, '__wrapped__'):
        view = view.__wrapped__
    monkeypatch.setattr(servers_api, 'get_jwt_identity', lambda: 1)
    with app.test_request_context():
        resp, status = view('srv')
    assert status == 404
    assert resp.get_json()['code'] == 'MAIL_SERVER_NOT_INSTALLED'
