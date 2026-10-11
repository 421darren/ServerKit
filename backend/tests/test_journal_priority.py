"""The journal endpoint only accepts journalctl levels 0-7 as priority."""
from unittest.mock import patch

import pytest

from factories import headers_for, make_user

OK = {'success': True, 'lines': [], 'source': 'journalctl'}


@pytest.fixture
def headers(app):
    from app import db
    return headers_for(make_user(db, 'jp_admin', 'admin'))


@pytest.mark.parametrize('value', ['8', '-1', 'err', '--file=/etc/shadow'])
def test_invalid_priority_is_400(client, headers, value):
    with patch('app.api.logs.LogService.get_journalctl_logs', return_value=OK) as read:
        resp = client.get(f'/api/v1/logs/journal?priority={value}', headers=headers)
    assert resp.status_code == 400
    assert read.call_count == 0


@pytest.mark.parametrize('value,passed', [('3', '3'), ('', None)])
def test_valid_or_absent_priority_reaches_journalctl(client, headers, value, passed):
    with patch('app.api.logs.LogService.get_journalctl_logs', return_value=OK) as read:
        resp = client.get(f'/api/v1/logs/journal?priority={value}', headers=headers)
    assert resp.status_code == 200
    assert read.call_args.args[3] == passed
