"""Socket.IO origin check: configured origins plus same-origin."""
from app.sockets import make_origin_checker

ENV_HTTPS = {'HTTP_HOST': 'panel.example.com', 'HTTP_X_FORWARDED_PROTO': 'https', 'wsgi.url_scheme': 'http'}


def test_same_origin_is_accepted_even_when_list_does_not_name_it():
    check = make_origin_checker(['http://localhost', 'https://localhost'])
    assert check('https://panel.example.com', ENV_HTTPS) is True


def test_configured_origin_is_accepted():
    check = make_origin_checker(['https://other.example.com'])
    assert check('https://other.example.com', ENV_HTTPS) is True


def test_foreign_origin_is_rejected():
    check = make_origin_checker(['http://localhost'])
    assert check('https://evil.example.net', ENV_HTTPS) is False


def test_scheme_mismatch_is_rejected():
    check = make_origin_checker([])
    assert check('http://panel.example.com', ENV_HTTPS) is False


def test_missing_origin_header_is_accepted_for_non_browser_clients():
    check = make_origin_checker([])
    assert check(None, ENV_HTTPS) is True


def test_wildcard_stays_wildcard():
    assert make_origin_checker('*') == '*'
    assert make_origin_checker(['*']) == '*'
