"""The legacy deploy webhook token must match exactly, in constant time,
and a missing token must never match a missing token."""
import pytest

from app.services.git_service import GitService


@pytest.mark.parametrize('configured,sent,ok', [
    ('tok-123', 'tok-123', True),
    ('tok-123', 'tok-124', False),
    ('tok-123', '', False),
    ('tok-123', None, False),
    (None, None, False),
    ('', '', False),
    (None, '', False),
])
def test_token_check(monkeypatch, configured, sent, ok):
    monkeypatch.setattr(GitService, 'get_app_config',
                        classmethod(lambda cls, app_id: {'webhook_token': configured}))
    assert GitService.verify_webhook(1, sent) is ok
