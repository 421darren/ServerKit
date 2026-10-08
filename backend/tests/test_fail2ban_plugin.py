"""Tests for the Fail2ban plugin input guards (manual ban/unban)."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'plugins',
                     'serverkit-fail2ban', 'fail2ban.py')
_spec = importlib.util.spec_from_file_location('f2b_plugin_under_test', _PATH)
f2b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f2b)


@pytest.mark.parametrize('value,expected', [
    ('192.0.2.55', '192.0.2.55'),
    (' 203.0.113.9 ', '203.0.113.9'),
    ('2001:db8::1', '2001:db8::1'),
    ('not-an-ip', None),
    ('1.2.3.4; id', None),
    ('', None),
    ('127.0.0.1', None),
    ('::1', None),
    ('0.0.0.0', None),
    ('224.0.0.1', None),
])
def test_validate_ip(value, expected):
    assert f2b.validate_ip(value) == expected


@pytest.mark.parametrize('name,ok', [
    ('sshd', True), ('nginx-http-auth', True), ('site_1.login', True),
    ('sshd; id', False), ('', False), ('a b', False), ('x' * 65, False),
])
def test_valid_jail_name(name, ok):
    assert f2b.valid_jail_name(name) is ok


def _boom(*a, **k):
    raise AssertionError('fail2ban-client must not be called')


def test_ban_rejects_invalid_ip_without_running_command(monkeypatch):
    monkeypatch.setattr(f2b, 'run_checked', _boom)
    r = f2b.Fail2banOps.ban_ip('not-an-ip')
    assert r['success'] is False


def test_ban_rejects_bad_jail_without_running_command(monkeypatch):
    monkeypatch.setattr(f2b, 'run_checked', _boom)
    assert f2b.Fail2banOps.ban_ip('192.0.2.1', 'sshd; id')['success'] is False


def test_ban_refuses_own_connection(monkeypatch):
    monkeypatch.setattr(f2b, 'run_checked', _boom)
    r = f2b.Fail2banOps.ban_ip('198.51.100.7', 'sshd', protected={'198.51.100.7'})
    assert r['success'] is False
    assert 'own connection' in r['error']


def test_ban_refuses_server_address(monkeypatch):
    monkeypatch.setattr(f2b, 'run_checked', _boom)
    monkeypatch.setattr(f2b, 'local_addresses', lambda: {'203.0.113.10'})
    assert f2b.Fail2banOps.ban_ip('203.0.113.10')['success'] is False


def test_ban_valid_ip_runs_command_with_clean_value(monkeypatch):
    calls = []

    def fake(cmd, timeout=10):
        calls.append(cmd)
        return {'success': True, 'error': ''}

    monkeypatch.setattr(f2b, 'run_checked', fake)
    monkeypatch.setattr(f2b, 'local_addresses', lambda: set())
    r = f2b.Fail2banOps.ban_ip(' 192.0.2.55 ', 'sshd')
    assert r['success'] is True
    assert calls == [['fail2ban-client', 'set', 'sshd', 'banip', '192.0.2.55']]
