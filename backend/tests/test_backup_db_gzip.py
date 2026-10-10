"""Database dumps must be real gzip, and restores must feed the client SQL.

Passing a ``gzip.open()`` handle as a subprocess stream hands the child the
raw fd: dumps came out as plain SQL inside a gzip header, and restores
piped compressed bytes into mysql/psql. These run real child processes —
small Python stand-ins for mysqldump/mysql — so the bytes really cross a pipe.
"""
import gzip
import sys

import pytest

from app.utils.system import run_from_gzip, run_to_gzip

_ROW = "INSERT INTO t VALUES (1), (2);\n"
_COUNT = 40000  # ~1.2 MB: more than a pipe buffer and more than one copy chunk
SQL = _ROW * _COUNT
# The child builds the dump itself — Windows caps a command line at 32K.
WRITE_SQL = f'import sys; sys.stdout.write({_ROW!r} * {_COUNT})'


def test_run_to_gzip_writes_real_gzip(tmp_path):
    dest = tmp_path / 'db.sql.gz'
    result = run_to_gzip(
        [sys.executable, '-c', WRITE_SQL], str(dest))
    assert result['success'], result
    with gzip.open(dest, 'rt') as f:
        assert f.read() == SQL


def test_run_to_gzip_failure_removes_partial_file(tmp_path):
    dest = tmp_path / 'db.sql.gz'
    result = run_to_gzip(
        [sys.executable, '-c', 'import sys; print("partial"); '
                               'sys.stderr.write("access denied"); sys.exit(2)'],
        str(dest))
    assert not result['success']
    assert result['returncode'] == 2
    assert 'access denied' in result['error']
    assert not dest.exists()


def test_run_from_gzip_feeds_decompressed_sql(tmp_path):
    src, out = tmp_path / 'db.sql.gz', tmp_path / 'received.sql'
    with gzip.open(src, 'wt') as f:
        f.write(SQL)
    result = run_from_gzip(
        [sys.executable, '-c',
         f'import sys; open({str(out)!r}, "wb").write(sys.stdin.buffer.read())'],
        str(src))
    assert result['success'], result
    assert out.read_text() == SQL


def test_run_from_gzip_child_exiting_early_reports_its_exit(tmp_path):
    src = tmp_path / 'db.sql.gz'
    with gzip.open(src, 'wt') as f:
        f.write(SQL * 5)
    result = run_from_gzip(
        [sys.executable, '-c', 'import sys; sys.stderr.write("syntax error"); sys.exit(1)'],
        str(src))
    assert not result['success']
    assert result['returncode'] == 1


@pytest.fixture
def fake_clients(tmp_path, monkeypatch):
    """Route mysqldump/mysql to Python stand-ins; mysql records its stdin."""
    received = tmp_path / 'mysql_stdin.sql'
    stand_ins = {
        'mysqldump': WRITE_SQL,
        'mysql': f'import sys; open({str(received)!r}, "wb").write(sys.stdin.buffer.read())',
    }

    def stand_in(runner):
        # Swap the binary, keep the real runner: the bytes still cross a pipe.
        return lambda cmd, *args, **kwargs: runner(
            [sys.executable, '-c', stand_ins[cmd[0]]], *args, **kwargs)

    monkeypatch.setattr('app.services.backup_service.run_to_gzip', stand_in(run_to_gzip))
    monkeypatch.setattr('app.services.backup_service.run_from_gzip', stand_in(run_from_gzip))
    monkeypatch.setattr('app.services.backup_service.is_command_available', lambda c: True)
    return received


def test_mysql_backup_then_restore_round_trips(app, tmp_path, fake_clients):
    from app.services.backup_service import BackupService
    backup = BackupService._backup_database_internal(
        'mysql', 'shop', str(tmp_path), {'user': 'root', 'password': 'pw'})
    assert backup['success'], backup
    with gzip.open(backup['path'], 'rt') as f:
        assert f.read() == SQL

    restored = BackupService.restore_database(backup['path'], 'mysql', 'shop',
                                              user='root', password='pw')
    assert restored['success'], restored
    assert fake_clients.read_text() == SQL
