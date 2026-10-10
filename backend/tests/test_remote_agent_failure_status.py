"""Remote Docker routes report why an agent command failed.

The cron proxy answered an offline agent with 503 and a refused command
with 403, but 22 of the 24 Docker proxy routes answered 500 for both, so
the UI could not tell "agent offline" from a crash.
"""
from unittest.mock import patch

import pytest

from factories import headers_for, make_server, make_user


@pytest.fixture
def ctx(app):
    from app import db
    return headers_for(make_user(db, 'af_admin', 'admin')), make_server(db, name='af-box').id


@pytest.mark.parametrize('code,status', [
    ('AGENT_OFFLINE', 503), ('PERMISSION_DENIED', 403), ('TIMEOUT', 500)])
@pytest.mark.parametrize('method,path,service_fn', [
    ('post', '/docker/containers/c1/start', 'start_container'),
    ('get', '/docker/images', 'list_images'),
    ('post', '/docker/compose/up', 'compose_up'),
])
def test_failure_status_follows_the_agent_code(client, ctx, code, status, method, path, service_fn):
    headers, server_id = ctx
    failure = {'success': False, 'code': code, 'error': 'nope'}
    with patch(f'app.services.remote_docker_service.RemoteDockerService.{service_fn}', return_value=failure):
        resp = getattr(client, method)(f'/api/v1/servers/{server_id}{path}', headers=headers,
                                       json={'project_path': '/srv/app'})
    assert resp.status_code == status
    assert resp.get_json()['code'] == code
