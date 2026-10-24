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
        'app.bootstrap.agents': {'start_agent_runtime': record('agents')},
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
    assert runtime_calls == ['recover', 'agents', 'metrics', 'webhooks', 'notifications',
                             'analytics', 'handlers', 'jobs', 'monitoring',
                             'uptime', 'linked', 'relay']


def test_monitor_failure_does_not_prevent_other_runtime_services(runtime_calls):
    def fail(_app):
        raise RuntimeError('monitor unavailable')
    sys.modules['app.services.monitoring_service'].MonitoringService.resume_if_enabled = fail
    logger = Mock()
    runtime.start_runtime(SimpleNamespace(config={}, logger=logger))
    logger.exception.assert_called_once()
    assert runtime_calls[-3:] == ['uptime', 'linked', 'relay']


def test_agent_maintenance_runs_only_in_server_mode(monkeypatch):
    from app.bootstrap.agents import start_agent_runtime
    from app.services.agent_registry import agent_registry
    from app.services.nonce_service import nonce_service
    from app.services.anomaly_detection_service import anomaly_detection_service

    heartbeat, nonces, anomalies = Mock(), Mock(), Mock()
    monkeypatch.setattr(agent_registry, 'start', heartbeat)
    monkeypatch.setattr(nonce_service, 'start_cleanup', nonces)
    monkeypatch.setattr(anomaly_detection_service, 'start_cleanup', anomalies)
    start_agent_runtime(SimpleNamespace(config={'TESTING': True}))
    assert not any(call.called for call in (heartbeat, nonces, anomalies))
    server = SimpleNamespace(config={})
    start_agent_runtime(server)
    heartbeat.assert_called_once_with(server)
    nonces.assert_called_once_with()
    anomalies.assert_called_once_with()


@pytest.mark.parametrize('module_name,instance_name', [
    ('nonce_service', 'nonce_service'),
    ('anomaly_detection_service', 'anomaly_detection_service'),
])
def test_agent_cleanup_start_is_idempotent(monkeypatch, module_name, instance_name):
    import importlib
    import threading
    module = importlib.import_module(f'app.services.{module_name}')
    service = getattr(module, instance_name)
    thread = Mock()
    thread.is_alive.return_value = True
    constructor = Mock(return_value=thread)
    monkeypatch.setattr(service, '_cleanup_thread', None)
    monkeypatch.setattr(service, '_stop_cleanup', threading.Event())
    monkeypatch.setattr(module.threading, 'Thread', constructor)
    service.start_cleanup()
    service.start_cleanup()
    constructor.assert_called_once()
    thread.start.assert_called_once()


def test_heartbeat_runtime_captures_the_serving_app(monkeypatch):
    from app.services.agent_registry import agent_registry
    start = Mock()
    monkeypatch.setattr(agent_registry, '_start_heartbeat_checker', start)
    monkeypatch.setattr(agent_registry, '_app', None)
    server = object()
    agent_registry.start(server)
    assert agent_registry._app is server
    start.assert_called_once_with()


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
