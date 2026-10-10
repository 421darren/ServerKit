"""110 removes the retired no-op schedule and cancels its queued jobs,
leaving every other schedule and job alone."""
import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def _load():
    path = Path(__file__).parents[1] / 'migrations/versions/110_drop_workflow_schedules_job.py'
    spec = importlib.util.spec_from_file_location('m110', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retired_schedule_goes_and_queued_jobs_are_cancelled(tmp_path, monkeypatch):
    migration = _load()
    engine = sa.create_engine('sqlite:///' + (tmp_path / 'upgraded.db').as_posix())
    with engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE scheduled_jobs (id INTEGER PRIMARY KEY, name TEXT)')
        conn.exec_driver_sql('CREATE TABLE jobs (id INTEGER PRIMARY KEY, kind TEXT, status TEXT)')
        conn.exec_driver_sql("INSERT INTO scheduled_jobs VALUES (1, 'workflow-schedules'), "
                             "(2, 'auto-sync')")
        conn.exec_driver_sql("INSERT INTO jobs VALUES "
                             "(1, 'builtin.workflow_schedules', 'pending'), "
                             "(2, 'builtin.workflow_schedules', 'succeeded'), "
                             "(3, 'builtin.auto_sync', 'pending')")
        monkeypatch.setattr(migration, 'op', Operations(MigrationContext.configure(conn)))
        migration.upgrade()
        names = [r[0] for r in conn.exec_driver_sql('SELECT name FROM scheduled_jobs')]
        statuses = dict(conn.exec_driver_sql('SELECT id, status FROM jobs').all())
    engine.dispose()

    assert names == ['auto-sync']
    assert statuses == {1: 'cancelled', 2: 'succeeded', 3: 'pending'}


def test_handler_and_seed_are_gone():
    from app.jobs.builtin_handlers import _BUILTINS
    assert 'workflow-schedules' not in [name for _k, _f, name, _i, _d in _BUILTINS]
