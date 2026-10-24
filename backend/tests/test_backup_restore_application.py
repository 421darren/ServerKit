"""restore_application must put the files at restore_path — not at the app's
original directory name next to it — and must never lose the live copy."""
import json
import os
import tarfile

from app.services.backup_service import BackupService


def _make_backup(tmp_path, app_dir_name='myapp', files=None):
    src = tmp_path / 'src' / app_dir_name
    src.mkdir(parents=True)
    for name, body in (files or {'index.html': 'v1'}).items():
        (src / name).write_text(body)
    bdir = tmp_path / 'bk'
    bdir.mkdir()
    archive = bdir / 'files.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(src, arcname=app_dir_name)
    (bdir / 'backup.json').write_text(json.dumps(
        {'files_backup': str(archive), 'app_name': app_dir_name}))
    return bdir


def test_restores_into_a_custom_path(tmp_path):
    bdir = _make_backup(tmp_path)
    target = tmp_path / 'www' / 'restored'
    target.mkdir(parents=True)
    (target / 'live.txt').write_text('live')

    result = BackupService.restore_application(str(bdir), str(target))

    assert result['success'], result
    assert (target / 'index.html').read_text() == 'v1'
    assert not (target / 'live.txt').exists()
    assert not (tmp_path / 'www' / 'myapp').exists()
    previous = [p for p in os.listdir(tmp_path / 'www') if p.startswith('restored.backup_')]
    assert len(previous) == 1
    assert (tmp_path / 'www' / previous[0] / 'live.txt').read_text() == 'live'
    assert not [p for p in os.listdir(tmp_path / 'www') if p.startswith('.restore-')]


def test_restores_into_a_path_that_does_not_exist_yet(tmp_path):
    bdir = _make_backup(tmp_path)
    target = tmp_path / 'www' / 'fresh'

    result = BackupService.restore_application(str(bdir), str(target))

    assert result['success'], result
    assert (target / 'index.html').read_text() == 'v1'


def test_a_bad_archive_leaves_the_live_copy_in_place(tmp_path):
    bdir = tmp_path / 'bk'
    bdir.mkdir()
    archive = bdir / 'files.tar.gz'
    loose = tmp_path / 'loose.txt'
    loose.write_text('x')
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(loose, arcname='loose.txt')  # no top-level directory
    (bdir / 'backup.json').write_text(json.dumps(
        {'files_backup': str(archive), 'app_name': 'myapp'}))
    target = tmp_path / 'www' / 'site'
    target.mkdir(parents=True)
    (target / 'live.txt').write_text('live')

    result = BackupService.restore_application(str(bdir), str(target))

    assert not result['success']
    assert (target / 'live.txt').read_text() == 'live'
    assert os.listdir(tmp_path / 'www') == ['site']
