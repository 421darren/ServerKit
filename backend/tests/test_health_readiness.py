"""/system/health tells the truth and keeps deployment details to signed-in callers.

It always answered "healthy" (even with the database gone) and handed any
anonymous caller the canonical domain and whether secrets encryption is
configured.
"""
from unittest.mock import patch

from factories import headers_for, make_user

DETAILS = ('encryption_configured', 'canonical_domain', 'canonical_https_enabled', 'canonical_origin')


def test_anonymous_probe_gets_status_only(client):
    body = client.get('/api/v1/system/health').get_json()
    assert body['status'] == 'healthy'
    assert not any(k in body for k in DETAILS)


def test_signed_in_caller_gets_the_details(app, client):
    from app import db
    headers = headers_for(make_user(db, 'hr_user'))
    body = client.get('/api/v1/system/health', headers=headers).get_json()
    assert all(k in body for k in DETAILS)


def test_bad_token_is_treated_as_anonymous(client):
    resp = client.get('/api/v1/system/health', headers={'Authorization': 'Bearer nope'})
    assert resp.status_code == 200
    assert 'canonical_domain' not in resp.get_json()


def test_unreachable_database_is_503(app, client):
    from app import db
    with patch.object(db.session, 'execute', side_effect=RuntimeError('db gone')):
        resp = client.get('/api/v1/system/health')
    assert resp.status_code == 503
    assert resp.get_json()['status'] == 'unhealthy'
