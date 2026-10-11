"""Best-effort side effects may fail, but never silently.

Each of these was `except Exception: pass`: a lost "backup failed" alert,
a broken live deploy log (dead for the life of the process) and a missing
deploy log line all left no trace. They still must not raise.
"""
import logging
from unittest.mock import patch

from app.services import run_log_service
from app.services.backup_service import BackupService


def test_lost_backup_alert_is_logged_not_raised(app, caplog, monkeypatch):
    monkeypatch.setattr(BackupService, 'get_config', classmethod(
        lambda cls: {'notifications': {'on_failure': True}}))
    with patch('app.services.notification_service.NotificationService.send_all',
               side_effect=RuntimeError('bus down')), \
            caplog.at_level(logging.ERROR, logger='app.services.backup_service'):
        BackupService._send_backup_notification('Nightly', False, 'disk full')
    assert 'Could not send the backup notification for Nightly' in caplog.text
    assert 'bus down' in caplog.text


def test_broken_live_log_emit_is_reported_once(caplog, monkeypatch):
    monkeypatch.setattr(run_log_service, '_reported', set())
    emit = run_log_service._make_default_emit_log('deploy')
    with patch('app.sockets.emit_run_log', side_effect=RuntimeError('socket gone')), \
            caplog.at_level(logging.WARNING, logger='app.services.run_log_service'):
        for _ in range(5):
            emit('run-1', [{'message': 'x'}])
    assert caplog.text.count('Live deploy log emit failed') == 1


def test_missing_deploy_log_line_is_logged_not_raised(app, caplog):
    from app.services.manifest_apply_service import ManifestApplyService

    class Job:
        id = 42

    with patch('app.services.manifest_apply_service.db.session.begin_nested',
               side_effect=RuntimeError('locked')), \
            caplog.at_level(logging.WARNING, logger='app.services.manifest_apply_service'):
        ManifestApplyService._log(Job(), 3, 'info', 'step done')
    assert 'Could not write deploy log line for job 42 step 3' in caplog.text
