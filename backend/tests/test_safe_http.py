"""safe_http.post must refuse internal targets, connect to the address it
checked, never follow redirects, and cap the body it keeps."""
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.utils import safe_http
from app.utils.safe_http import UnsafeURLError, post, resolve_public

_real_getaddrinfo = socket.getaddrinfo


def _fake_dns(mapping):
    def getaddrinfo(host, port, *args, **kwargs):
        if host in mapping:
            family = socket.AF_INET6 if ':' in mapping[host] else socket.AF_INET
            return [(family, socket.SOCK_STREAM, 6, '', (mapping[host], port))]
        return _real_getaddrinfo(host, port, *args, **kwargs)
    return getaddrinfo


@pytest.mark.parametrize('ip', [
    '127.0.0.1', '10.0.0.5', '172.16.3.4', '192.168.1.1', '169.254.169.254',
    '100.64.0.1', '0.0.0.0', '::1', 'fd00::1', 'fe80::1', '::ffff:127.0.0.1',
    '::ffff:169.254.169.254', '224.0.0.1',
])
def test_internal_addresses_are_refused(monkeypatch, ip):
    monkeypatch.setattr(socket, 'getaddrinfo', _fake_dns({'hook.test': ip}))
    with pytest.raises(UnsafeURLError):
        resolve_public('https://hook.test/x')


def test_a_name_with_any_internal_answer_is_refused(monkeypatch):
    def getaddrinfo(host, port, *a, **k):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', port)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', port))]
    monkeypatch.setattr(socket, 'getaddrinfo', getaddrinfo)
    with pytest.raises(UnsafeURLError):
        resolve_public('https://hook.test/x')


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'gopher://x/', 'ftp://h/', '', 'http://'])
def test_non_http_urls_are_refused(url):
    with pytest.raises(UnsafeURLError):
        resolve_public(url)


def test_public_address_is_allowed(monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', _fake_dns({'hook.test': '93.184.216.34'}))
    parts, ip = resolve_public('https://hook.test/x')
    assert str(ip) == '93.184.216.34' and parts.hostname == 'hook.test'


def test_refused_before_any_connection(monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', _fake_dns({'hook.test': '169.254.169.254'}))
    monkeypatch.setattr(safe_http.requests, 'Session',
                        lambda: pytest.fail('a request was attempted'))
    with pytest.raises(UnsafeURLError):
        post('http://hook.test/latest/meta-data/')


@pytest.fixture
def server():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append({'host': self.headers['Host'], 'path': self.path,
                         'body': self.rfile.read(int(self.headers['Content-Length'] or 0))})
            if self.path == '/redirect':
                self.send_response(302)
                self.send_header('Location', 'http://169.254.169.254/')
                self.end_headers()
                return
            body = b'x' * (1024 * 1024) if self.path == '/big' else b'ok'
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1], seen
    httpd.shutdown()


def test_connects_to_the_checked_address_with_the_original_host(monkeypatch, server):
    port, seen = server
    monkeypatch.setenv(safe_http.ALLOW_PRIVATE_ENV, '1')
    monkeypatch.setattr(socket, 'getaddrinfo', _fake_dns({'hook.test': '127.0.0.1'}))
    resp = post(f'http://hook.test:{port}/in?a=1', data=b'payload')
    assert resp.status_code == 200 and resp.text == 'ok'
    assert seen == [{'host': f'hook.test:{port}', 'path': '/in?a=1', 'body': b'payload'}]


def test_redirects_are_not_followed(monkeypatch, server):
    port, seen = server
    monkeypatch.setenv(safe_http.ALLOW_PRIVATE_ENV, '1')
    resp = post(f'http://127.0.0.1:{port}/redirect')
    assert resp.status_code == 302
    assert len(seen) == 1


def test_response_body_is_capped(monkeypatch, server):
    port, _ = server
    monkeypatch.setenv(safe_http.ALLOW_PRIVATE_ENV, '1')
    resp = post(f'http://127.0.0.1:{port}/big', max_bytes=1000)
    assert len(resp.content) == 1000


def test_loopback_needs_the_opt_in(server):
    port, seen = server
    with pytest.raises(UnsafeURLError):
        post(f'http://127.0.0.1:{port}/in')
    assert seen == []


# The user-configured sinks all go through safe_http: the metadata address
# (an IP literal, so no DNS involved) must be refused by each of them.
METADATA = 'http://169.254.169.254/latest/meta-data/'
_ALERT = [{'type': 'cpu', 'severity': 'critical', 'message': 'hot', 'value': 99, 'threshold': 90}]


@pytest.mark.parametrize('sender', ['send_discord', 'send_slack', 'send_generic_webhook'])
def test_notification_webhooks_refuse_internal_urls(app, monkeypatch, sender):
    from app.services.notification_service import NotificationService
    monkeypatch.setattr(safe_http.requests, 'Session',
                        lambda: pytest.fail('a request was attempted'))
    result = getattr(NotificationService, sender)(
        _ALERT, {'enabled': True, 'webhook_url': METADATA, 'url': METADATA})
    assert result['success'] is False
    assert 'non-public' in result['error']


def test_gateway_forward_refuses_internal_urls(app, monkeypatch):
    from types import SimpleNamespace
    from app.services.webhook_gateway_service import WebhookGatewayService
    monkeypatch.setattr(safe_http.requests, 'Session',
                        lambda: pytest.fail('a request was attempted'))
    endpoint = SimpleNamespace(forward_url=METADATA, retry_count=1)
    delivery = SimpleNamespace(event_id='e1')
    result = WebhookGatewayService._forward(endpoint, delivery, b'{}', {})
    assert result['success'] is False
    assert 'non-public' in result['error']
