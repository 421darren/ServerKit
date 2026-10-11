"""A JSON body that is not an object is a 400, not a crash.

These routes read ``request.get_json()`` and went straight to
``data.get(...)``; a body of ``null`` or ``[]`` raised AttributeError /
TypeError and answered 500.
"""
import json

import pytest

from factories import headers_for, make_server, make_user


@pytest.fixture
def admin_headers(app):
    from app import db
    return headers_for(make_user(db, 'jo_admin', 'admin'))


@pytest.fixture
def server_id(app):
    from app import db
    return make_server(db, name='jo-box').id


ROUTES = [
    ('post', '/api/v1/cron/jobs'),
    ('post', '/api/v1/cron/jobs/job_x/toggle'),
    ('put', '/api/v1/servers/{sid}'),
    ('put', '/api/v1/servers/{sid}/allowed-ips'),
    ('post', '/api/v1/servers/fleet/upgrade'),
    ('post', '/api/v1/servers/fleet/rollout'),
]


@pytest.mark.parametrize('body', ['null', '[]', '"text"'])
@pytest.mark.parametrize('method,url', ROUTES)
def test_non_object_body_is_rejected(client, admin_headers, server_id, method, url, body):
    resp = getattr(client, method)(url.format(sid=server_id), data=body,
                                   headers={**admin_headers, 'Content-Type': 'application/json'})
    assert resp.status_code == 400, (url, resp.status_code, resp.get_data(as_text=True)[:200])
    assert resp.get_json()['code'] == 'validation.body_not_object'


def test_an_object_body_still_reaches_the_route(client, admin_headers):
    resp = client.post('/api/v1/cron/jobs/job_x/toggle', data=json.dumps({'enabled': False}),
                       headers={**admin_headers, 'Content-Type': 'application/json'})
    assert resp.status_code != 400 or resp.get_json().get('code') != 'validation.body_not_object'


def test_optional_body_may_be_absent(client, admin_headers):
    """Action routes read optional settings: no body (or no JSON content type)
    is an empty dict, exactly as `get_json(silent=True) or {}` gave."""
    resp = client.delete('/api/v1/setup-health/snooze?key=setup.canonical_domain',
                         headers=admin_headers)
    assert resp.status_code != 415
    assert (resp.get_json() or {}).get('code') != 'validation.body_not_object'


def test_optional_body_must_still_be_an_object(client, admin_headers):
    resp = client.delete('/api/v1/setup-health/snooze', data='[]',
                         headers={**admin_headers, 'Content-Type': 'application/json'})
    assert resp.status_code == 400
    assert resp.get_json()['code'] == 'validation.body_not_object'
