"""The password generator endpoint bounds its length parameter."""
import pytest

from factories import headers_for, make_user


@pytest.mark.parametrize('asked,got', [('1000000000', 128), ('2', 8), ('24', 24), ('', 16)])
def test_length_is_clamped(app, client, asked, got):
    from app import db
    headers = headers_for(make_user(db, f'gp_{asked or "default"}'))
    resp = client.get(f'/api/v1/databases/generate-password?length={asked}', headers=headers)
    assert resp.status_code == 200
    assert len(resp.get_json()['password']) == got
