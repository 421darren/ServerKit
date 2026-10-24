"""Regression gate for the "unguarded background writer" bug class.

create_app() must not spawn background threads under the testing config.
The app fixture is function-scoped, so any thread started per create_app()
call piles up one immortal copy per test — and if that thread writes to the
DB (analytics flush, metrics collection), the copies race the running test's
own transactions on the shared SQLite file and the suite fails with
intermittent "database is locked" errors in unrelated tests.

Background workers must either be gated on ``app.config['TESTING']`` (like
the queue-bus consumers) or started only by an explicit runtime trigger
(socket connect, API call), never as an unconditional create_app side effect.
"""
import threading

import pytest


def _thread_ids():
    return {t.ident for t in threading.enumerate()}


def _is_allowed(thread):
    """Library-internal housekeeping we can't gate: flask-limiter's in-memory
    storage arms a threading.Timer to expire rate-limit events. Memory-only."""
    fn = getattr(thread, 'function', None)  # threading.Timer callback
    return getattr(fn, '__module__', '').startswith('limits.')


def test_create_app_testing_spawns_no_background_threads():
    from app import create_app, db

    before = _thread_ids()
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        try:
            # Exercise the request hooks too — a per-request spawn (analytics
            # buffers, audit trails) must also stay inert under testing.
            client = app.test_client()
            client.get('/api/v1/system/health')

            leaked = [t.name for t in threading.enumerate()
                      if t.ident not in before and not _is_allowed(t)]
            assert leaked == [], (
                f'create_app(testing) spawned background thread(s): {leaked}. '
                'Gate the spawn on app.config["TESTING"] (see the queue-bus '
                'consumers) so per-test app instances do not leak writers '
                'that race the suite\'s shared database.')
        finally:
            db.session.remove()
            db.drop_all()


@pytest.mark.parametrize('failed_phase', [None, 'persistence', 'plugins'])
def test_factory_phase_order_and_context(monkeypatch, failed_phase):
    import app as application
    from flask import has_app_context
    from app.bootstrap import configuration, persistence, plugins, http, runtime
    import app.sockets
    import app.agent_gateway
    import app.core_blueprints
    from app.services import recycle_bin_service, restore_point_adapters

    calls = []
    def phase(name, context=False):
        def run(*args):
            assert has_app_context() is context
            calls.append(name)
            if name == failed_phase:
                raise RuntimeError('startup failed')
        return run

    monkeypatch.setattr(configuration, 'configure_application', phase('configuration'))
    monkeypatch.setattr(app.sockets, 'init_socketio', phase('socket'))
    monkeypatch.setattr(app.agent_gateway, 'init_agent_gateway', phase('gateway'))
    monkeypatch.setattr(app.core_blueprints, 'register_core_blueprints', phase('routes'))
    monkeypatch.setattr(recycle_bin_service, 'register_builtin_types', phase('recycle'))
    monkeypatch.setattr(restore_point_adapters, 'register_builtin_restore_point_adapters', phase('restore'))
    monkeypatch.setattr(persistence, 'prepare_persistence', phase('persistence', True))
    monkeypatch.setattr(plugins, 'load_extensions', phase('plugins', True))
    monkeypatch.setattr(runtime, 'start_runtime', phase('runtime', True))
    monkeypatch.setattr(http, 'register_http_handlers', phase('http'))
    monkeypatch.setattr(application, 'socketio', application.socketio)
    expected = ['configuration', 'socket', 'gateway', 'routes', 'recycle',
                'restore', 'persistence', 'plugins', 'runtime', 'http']
    if failed_phase:
        with pytest.raises(RuntimeError, match='startup failed'):
            application.create_app('testing')
        assert calls == expected[:expected.index(failed_phase) + 1]
    else:
        application.create_app('testing')
        assert calls == expected
