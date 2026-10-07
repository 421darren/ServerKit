"""Application backups must fail loudly instead of archiving nothing."""
import os
import pytest

from app.services.backup_service import BackupService


def test_missing_folder_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='does not exist'):
        BackupService._assert_archivable('x', str(tmp_path / 'nope'))


def test_empty_folder_is_rejected(tmp_path):
    (tmp_path / 'sub').mkdir()
    with pytest.raises(ValueError, match='contains no files'):
        BackupService._assert_archivable('x', str(tmp_path))


def test_empty_path_is_rejected():
    with pytest.raises(ValueError):
        BackupService._assert_archivable('x', '')


def test_folder_with_a_file_is_accepted(tmp_path):
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'a.txt').write_text('hi')
    BackupService._assert_archivable('x', str(tmp_path))
