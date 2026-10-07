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


def test_named_docker_volumes_are_rejected(tmp_path):
    (tmp_path / 'docker-compose.yml').write_text(
        "services:\n  wp:\n    image: wordpress\n    volumes:\n      - wordpress_html:/var/www/html\n"
        "volumes:\n  wordpress_html:\n"
    )
    with pytest.raises(ValueError, match='Docker volumes'):
        BackupService._assert_archivable('wp', str(tmp_path))


def test_bind_mounts_inside_the_folder_are_accepted(tmp_path):
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data' / 'x.txt').write_text('hi')
    (tmp_path / 'docker-compose.yml').write_text(
        "services:\n  app:\n    image: x\n    volumes:\n      - ./data:/data\n"
    )
    BackupService._assert_archivable('app', str(tmp_path))
