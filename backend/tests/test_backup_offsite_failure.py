"""A scheduled backup that was told to go offsite and didn't is a failure.

The upload helpers report failure in their return value, which the
scheduler ignored, so the schedule read 'success' and no "backup failed"
notification went out while the only copy sat on the box being backed up.
"""
import pytest

from app.services.backup_service import BackupService
from app.services.storage_provider_service import StorageProviderService

SCHED = {'id': 's1', 'name': 'Nightly', 'backup_type': 'files',
         'target': '/srv/data', 'upload_remote': True}


@pytest.fixture
def run(app, tmp_path, monkeypatch):
    archive = tmp_path / 'files.tar.gz'
    archive.write_bytes(b'x')
    config = {'schedules': [dict(SCHED)]}
    notified = []
    monkeypatch.setattr(BackupService, 'get_config', classmethod(lambda cls: config))
    monkeypatch.setattr(BackupService, 'save_config', classmethod(lambda cls, c: c))
    monkeypatch.setattr(BackupService, 'backup_files', classmethod(
        lambda cls, paths, backup_name=None: {'success': True, 'path': str(archive)}))
    monkeypatch.setattr(BackupService, '_send_backup_notification', classmethod(
        lambda cls, name, ok, message, correlation_id=None: notified.append((ok, message))))

    def go(upload_result):
        monkeypatch.setattr(StorageProviderService, 'upload_file',
                            classmethod(lambda cls, path, remote_key=None: upload_result))
        BackupService._run_scheduled_backup(dict(SCHED))
        return config['schedules'][0]['last_status'], notified

    return go


def test_failed_offsite_upload_fails_the_backup_and_notifies(run):
    status, notified = run({'success': False, 'error': 'AccessDenied'})
    assert status == 'failed'
    assert len(notified) == 1 and notified[0][0] is False
    assert 'offsite upload failed: AccessDenied' in notified[0][1]
    assert 'Saved locally at' in notified[0][1]


def test_successful_offsite_upload_stays_a_success(run):
    status, notified = run({'success': True, 'remote_key': 'k'})
    assert status == 'success'
    assert notified == []
