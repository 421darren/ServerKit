"""/2fa/verify must honour the account lockout and must not accept the same
TOTP code, or the same pending-login token, twice."""
import time
from datetime import datetime, timedelta

import pyotp
import pytest

from factories import make_user


@pytest.fixture(autouse=True)
def _fresh_state(app):
    from app import limiter
    from app.api import two_factor
    spent = getattr(two_factor, '_spent', {})
    limiter.reset()
    spent.clear()
    yield
    limiter.reset()
    spent.clear()


@pytest.fixture
def mfa_user(db_session):
    return make_user(db_session, password='password123', totp_enabled=True,
                     totp_secret=pyotp.random_base32())


def _pending(client, user):
    resp = client.post('/api/v1/auth/login', json={'email': user.email, 'password': 'password123'})
    assert resp.status_code == 200 and resp.get_json()['requires_2fa']
    return resp.get_json()['temp_token']


def _verify(client, temp_token, code):
    return client.post('/api/v1/auth/2fa/verify', json={'temp_token': temp_token, 'code': code})


def test_a_totp_code_logs_in_only_once(client, mfa_user):
    code = pyotp.TOTP(mfa_user.totp_secret).now()
    assert _verify(client, _pending(client, mfa_user), code).status_code == 200
    replay = _verify(client, _pending(client, mfa_user), code)
    assert replay.status_code == 401
    assert 'access_token' not in replay.get_json()


def test_a_pending_token_completes_only_one_login(client, mfa_user):
    totp = pyotp.TOTP(mfa_user.totp_secret)
    temp = _pending(client, mfa_user)
    assert _verify(client, temp, totp.now()).status_code == 200
    # A different code that is also inside the valid window.
    again = _verify(client, temp, totp.at(time.time() + 30))
    assert again.status_code == 401
    assert 'access_token' not in again.get_json()


def test_a_locked_account_cannot_finish_with_a_correct_code(client, mfa_user):
    from app import db
    temp = _pending(client, mfa_user)
    mfa_user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()
    resp = _verify(client, temp, pyotp.TOTP(mfa_user.totp_secret).now())
    assert resp.status_code == 429
    assert 'access_token' not in resp.get_json()
