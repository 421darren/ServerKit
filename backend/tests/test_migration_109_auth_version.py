"""109 replaces the guessable backfilled auth_version '0' with a random epoch
per user, and leaves already-random epochs alone."""
import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def _load():
    path = Path(__file__).parents[1] / 'migrations/versions/109_randomize_legacy_auth_version.py'
    spec = importlib.util.spec_from_file_location('m109', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_epochs_become_random_and_distinct(tmp_path, monkeypatch):
    migration = _load()
    engine = sa.create_engine('sqlite:///' + (tmp_path / 'upgraded.db').as_posix())
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE users (id INTEGER PRIMARY KEY, auth_version TEXT)')
        conn.exec_driver_sql("INSERT INTO users VALUES (1, '0'), (2, '0'), (3, ''), "
                             "(4, NULL), (5, 'a1b2c3d4e5f60718293a4b5c6d7e8f90')")
        monkeypatch.setattr(migration, 'op', Operations(MigrationContext.configure(conn)))
        migration.upgrade()
        rows = dict(conn.exec_driver_sql('SELECT id, auth_version FROM users').all())
    engine.dispose()

    rotated = [rows[i] for i in (1, 2, 3, 4)]
    assert all(v and len(v) == 32 and v != '0' for v in rotated)
    assert len(set(rotated)) == 4
    assert rows[5] == 'a1b2c3d4e5f60718293a4b5c6d7e8f90'
