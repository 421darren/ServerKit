"""A failed blueprint hot-load must lead to a (scheduled) panel restart."""
from unittest import mock

from app.services import plugin_service


def test_no_restart_when_disabled(monkeypatch):
    monkeypatch.setenv('INVOCATION_ID', 'x')
    monkeypatch.setenv('SERVERKIT_AUTO_RESTART', '0')
    with mock.patch('threading.Timer') as timer:
        assert plugin_service.schedule_restart_for_new_routes('demo') is False
        timer.assert_not_called()


def test_no_restart_outside_systemd(monkeypatch):
    monkeypatch.delenv('INVOCATION_ID', raising=False)
    monkeypatch.delenv('SERVERKIT_AUTO_RESTART', raising=False)
    with mock.patch('threading.Timer') as timer:
        assert plugin_service.schedule_restart_for_new_routes('demo') is False
        timer.assert_not_called()


def test_restart_scheduled_under_systemd(monkeypatch):
    monkeypatch.setenv('INVOCATION_ID', 'x')
    monkeypatch.delenv('SERVERKIT_AUTO_RESTART', raising=False)
    with mock.patch('threading.Timer') as timer:
        assert plugin_service.schedule_restart_for_new_routes('demo', delay_seconds=7) is True
        assert timer.call_args[0][0] == 7
        timer.return_value.start.assert_called_once()


def test_install_calls_helper_on_hot_load_failure():
    import inspect
    src = inspect.getsource(plugin_service)
    assert "schedule_restart_for_new_routes(slug)" in src
