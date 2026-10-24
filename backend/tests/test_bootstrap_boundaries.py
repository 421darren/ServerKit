"""Startup ordering and dependency boundaries, without launching workers."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.bootstrap import runtime


@pytest.fixture
def runtime_calls(monkeypatch):
    calls = []

    def record(name, result=None):
        def call(*args, **kwargs):
            calls.append(name)
            return result
        return call

    modules = {
        'app.jobs.service': {'JobService': SimpleNamespace(recover_interrupted=record('recover'))},
        'app.services.metrics_history_service': {'MetricsHistoryService': SimpleNamespace(
            is_running=lambda: False, start_collection=record('metrics'))},
        'app.queue_bus.consumers': {'start_webhook_consumer': record('webhooks')},
        'app.notifications.consumer': {'start_notification_consumer': record('notifications')},
        'app.middleware.api_analytics': {'start_analytics_flush_thread': record('analytics')},
        'app.jobs': {'start_job_system': record('jobs')},
        'app.bootstrap.jobs': {'register_job_handlers': record('handlers')},
        'app.services.monitoring_service': {'MonitoringService': SimpleNamespace(resume_if_enabled=record('monitoring'))},
        'app.services.uptime_service': {'UptimeService': SimpleNamespace(resume_if_enabled=record('uptime'))},
        'app.services.linked_panel_service': {'LinkedPanelService': SimpleNamespace(start_client_if_linked=record('linked'))},
    }
    for name, attrs in modules.items():
        monkeypatch.setitem(sys.modules, name, SimpleNamespace(**attrs))
    from app import services
    monkeypatch.setattr(services, 'connect_client', SimpleNamespace(
        start_client_if_paired=record('relay')), raising=False)
    monkeypatch.delenv('SERVERKIT_SKIP_BACKGROUND', raising=False)
    monkeypatch.setattr(sys, 'argv', ['gunicorn'])
    return calls


@pytest.mark.parametrize('argv,skip', [(['flask', 'db', 'upgrade'], None),
                                     (['flask'], None), (['gunicorn'], '1')])
def test_one_shot_startup_never_recovers_or_starts_workers(monkeypatch, runtime_calls, argv, skip):
    monkeypatch.setattr(sys, 'argv', argv)
    if skip:
        monkeypatch.setenv('SERVERKIT_SKIP_BACKGROUND', skip)
    runtime.start_runtime(SimpleNamespace(config={}, logger=Mock()))
    assert runtime_calls == []


@pytest.mark.parametrize('argv', [['gunicorn'], ['flask', 'run']])
def test_recovery_precedes_consumers_and_handlers_precede_jobs(monkeypatch, runtime_calls, argv):
    monkeypatch.setattr(sys, 'argv', argv)
    runtime.start_runtime(SimpleNamespace(config={}, logger=Mock()))
    assert runtime_calls == ['recover', 'metrics', 'webhooks', 'notifications',
                             'analytics', 'handlers', 'jobs', 'monitoring',
                             'uptime', 'linked', 'relay']


def test_factory_phase_order_and_context(monkeypatch):
    import app as application
    from flask import has_app_context
    from app.bootstrap import configuration, persistence, plugins, http
    import app.sockets
    import app.agent_gateway
    import app.core_blueprints
    from app.services import recycle_bin_service, restore_point_adapters

    calls = []
    def phase(name, context=False):
        def run(*args):
            assert has_app_context() is context
            calls.append(name)
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
    application.create_app('testing')
    assert calls == ['configuration', 'socket', 'gateway', 'routes', 'recycle',
                     'restore', 'persistence', 'plugins', 'runtime', 'http']


def test_bootstrap_is_an_assembly_layer_not_a_service_dependency():
    root = Path(__file__).parents[1] / 'app'
    for folder in ('api', 'services', 'models', 'jobs'):
        for path in (root / folder).rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or '').startswith('app.bootstrap'), path
                elif isinstance(node, ast.Import):
                    assert not any(a.name.startswith('app.bootstrap') for a in node.names), path
    factory = ast.parse((root / '__init__.py').read_text(encoding='utf-8'))
    create = next(n for n in factory.body if isinstance(n, ast.FunctionDef) and n.name == 'create_app')
    assert create.end_lineno - create.lineno < 70, 'Keep feature setup in an owned bootstrap phase'
    for node in ast.walk(create):
        assert not isinstance(node, (ast.Try, ast.For, ast.While)), 'Factory must compose phases'
