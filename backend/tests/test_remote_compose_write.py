"""Remote compose failures and plain-text file writes (panel side)."""
import base64
from unittest.mock import patch

from app.api import servers as srv


def _app_ctx(app):
    return app.test_request_context('/')


def test_compose_result_inner_failure_is_http_500(app):
    with _app_ctx(app):
        resp, code = srv._compose_result(
            {'success': True, 'data': {'success': False, 'error': 'build failed'}})
        assert code == 500
        assert resp.get_json()['error'] == 'build failed'


def test_compose_result_ok_passthrough(app):
    with _app_ctx(app):
        resp = srv._compose_result({'success': True, 'data': {'success': True}})
        assert resp.get_json()['success'] is True


def test_compose_result_dispatch_failure_is_500(app):
    with _app_ctx(app):
        resp, code = srv._compose_result({'success': False, 'error': 'offline'})
        assert code == 500


def test_write_content_text_is_base64_encoded():
    out = srv._encode_write_content({'content': 'h\u00e9llo', 'encoding': 'text'})
    assert base64.b64decode(out).decode('utf-8') == 'h\u00e9llo'


def test_write_content_default_is_passthrough():
    assert srv._encode_write_content({'content': 'aGk='}) == 'aGk='
