"""Monitoring and uptime tracking survive a restart.

Both loops were only ever started by an API call, so every panel restart
silently stopped alerting while the UI still showed monitoring enabled.
The monitor loop also ran without an app context, so its telemetry and
in-app notification writes raised and were swallowed.
"""
import threading

import pytest
from flask import has_app_context

from app.services.monitoring_service import MonitoringService
from app.services.uptime_service import UptimeService


@pytest.fixture
def monitoring(monkeypatch):
    config = {'enabled': True, 'check_interval': 0}
    seen, ran = [], threading.Event()

    def check():
        seen.append(has_app_context())
        MonitoringService._stop_monitoring = True
        ran.set()
        return []

    monkeypatch.setattr(MonitoringService, 'get_config', classmethod(lambda cls: config))
    monkeypatch.setattr(MonitoringService, 'save_config', classmethod(lambda cls, c: True))
    monkeypatch.setattr(MonitoringService, 'check_thresholds', classmethod(lambda cls: check()))
    monkeypatch.setattr(MonitoringService, '_monitoring_thread', None)
    yield config, seen, ran
    MonitoringService._stop_monitoring = True


def test_monitoring_left_on_resumes_in_an_app_context(app, monitoring):
    config, seen, ran = monitoring
    MonitoringService.resume_if_enabled(app)
    assert ran.wait(10)
    assert seen == [True]


def test_monitoring_left_off_stays_off(app, monitoring):
    config, seen, ran = monitoring
    config['enabled'] = False
    MonitoringService.resume_if_enabled(app)
    assert MonitoringService._monitoring_thread is None


@pytest.fixture
def uptime(tmp_path, monkeypatch):
    monkeypatch.setattr(UptimeService, 'DATA_DIR', str(tmp_path))
    monkeypatch.setattr(UptimeService, 'UPTIME_FILE', str(tmp_path / 'uptime.json'))
    monkeypatch.setattr(UptimeService, '_tracking_thread', None)
    # A loop that exits at once: the test is about who starts it.
    monkeypatch.setattr(UptimeService, '_tracking_loop', classmethod(lambda cls: None))
    started = []
    real_start = UptimeService.start_tracking.__func__

    def counting_start(cls):
        started.append(True)
        return real_start(cls)

    monkeypatch.setattr(UptimeService, 'start_tracking', classmethod(counting_start))
    return started


def _restart():
    UptimeService._tracking_thread = None


def test_uptime_tracking_resumes_after_restart(uptime):
    UptimeService.start_tracking()
    _restart()
    UptimeService.resume_if_enabled()
    assert len(uptime) == 2


def test_stopped_uptime_tracking_stays_stopped(uptime):
    UptimeService.start_tracking()
    UptimeService.stop_tracking()
    _restart()
    UptimeService.resume_if_enabled()
    assert len(uptime) == 1


def test_never_started_uptime_tracking_stays_off(uptime):
    UptimeService.resume_if_enabled()
    assert uptime == []


def test_resume_does_not_create_an_uncreatable_data_dir(uptime, tmp_path, monkeypatch):
    """The image runs unprivileged and cannot create /var/lib/serverkit; boot
    called resume and crashed on that makedirs before serving anything."""
    blocker = tmp_path / 'not-a-dir'
    blocker.write_text('')
    data_dir = blocker / 'serverkit'           # makedirs here always fails
    monkeypatch.setattr(UptimeService, 'DATA_DIR', str(data_dir))
    monkeypatch.setattr(UptimeService, 'UPTIME_FILE', str(data_dir / 'uptime_history.json'))
    UptimeService.resume_if_enabled()
    assert uptime == [] and not data_dir.exists()
