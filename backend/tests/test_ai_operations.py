"""Agent workflow contracts: approve, queue, observe, verify and reconnect.

The real registry, Recipe engine and deployment records run against SQLite.
Only infrastructure I/O is replaced; no model key or Docker daemon is needed.
"""
import copy
from contextlib import contextmanager

import pytest

from app import db
from app.exceptions import ValidationError
from app.models.deployment_job import DeploymentJob
from app.services import ai_operations as ops, ai_service
from app.services.ai_tools_builtin import register_builtin_tools, tool_caller
from app.services.ai_tool_registry import ai_tool_registry
from app.services.deployment_job_service import DeploymentJobService
from app.services.template_service import TemplateService
from factories import make_application, make_user


@contextmanager
def caller(user):
    token = tool_caller.set(user)
    try:
        yield
    finally:
        tool_caller.reset(token)


@pytest.fixture
def setup(app, monkeypatch):
    with app.app_context():
        user = make_user(db, role='admin')
        template = {'name': 'Example', 'version': '1', 'compose': {'services': {'web': {'image': 'nginx'}}},
                    'variables': {'TITLE': {'type': 'string'}, 'PASSWORD': {'type': 'password'}}}
        monkeypatch.setattr(TemplateService, 'get_template', lambda ident: {'success': True, 'template': copy.deepcopy(template)})
        monkeypatch.setattr(TemplateService, 'build_install_plan', lambda *a, **kw: {
            'success': True,
            'template': {**template, 'auto_domain': True} if kw.get('auto_domain') else copy.deepcopy(template),
            'variables': {'PASSWORD': 'generated-do-not-leak'}, 'plan': {'steps': []}})
        queued = []
        monkeypatch.setattr(DeploymentJobService, '_enqueue_registered', lambda job: queued.append(job.id))
        monkeypatch.setattr(ai_service, '_pii_enabled', lambda: False)
        register_builtin_tools()
        yield user, template, queued


def prepare(user):
    with caller(user):
        return ops.prepare_template_deployment('nginx', 'demo-app', 'local', {'TITLE': 'Demo'})


def test_preview_is_read_only_and_roundtrips_through_privacy_filter(setup):
    user, _, queued = setup
    descriptor = ai_tool_registry.get('core__prepare_template_deployment')
    result = ai_service._make_read_wrapper(descriptor, user)(
        template_id='nginx', app_name='demo-app', server_id='local')
    assert result['success']
    assert ops.decode_proposal(result['proposal'], user)['app_name'] == 'demo-app'
    assert 'generated-do-not-leak' not in str(result)
    assert DeploymentJob.query.count() == 0
    assert not queued


def test_proposal_rejects_tampering_other_user_and_expiry(setup, monkeypatch):
    user, _, _ = setup
    proposal = prepare(user)['proposal']
    with pytest.raises(ValidationError):
        ops.decode_proposal(proposal + 'changed', user)
    other = make_user(db, role='admin')
    with pytest.raises(PermissionError):
        ops.decode_proposal(proposal, other)
    monkeypatch.setattr(ops, 'PROPOSAL_TTL', -1)
    with pytest.raises(ValidationError):
        ops.decode_proposal(proposal, user)


def test_small_tool_budget_never_returns_a_truncated_proposal(setup, monkeypatch):
    from app.services import ai_management
    user, _, queued = setup
    monkeypatch.setattr(ai_management, 'settings', lambda: {'max_tool_result_length': 256})
    wrapper = ai_service._make_read_wrapper(ai_tool_registry.get('core__prepare_template_deployment'), user)
    result = wrapper(template_id='nginx', app_name='demo-app', server_id='local')
    assert not result['success']
    assert 'output limit' in result['error']
    assert 'proposal' not in result
    assert not queued


def test_secrets_and_unsafe_template_paths_are_rejected(setup):
    user, _, _ = setup
    with caller(user):
        with pytest.raises(ValidationError, match='credentials'):
            ops.prepare_template_deployment('nginx', 'demo-app', 'local', {'PASSWORD': 'secret'})
        with pytest.raises(ValidationError):
            ops.get_deployment_template('../private')
        with pytest.raises(ValidationError):
            ops.prepare_template_deployment('nginx', '../escape', 'local')


def test_changed_template_requires_new_approval(setup):
    user, template, queued = setup
    proposal = prepare(user)['proposal']
    template['version'] = '2'
    with caller(user), pytest.raises(ValidationError, match='changed'):
        ops.execute_deployment_proposal(proposal)
    assert not queued


def test_worker_rechecks_template_after_queueing(setup):
    user, template, _ = setup
    with caller(user):
        started = ops.execute_deployment_proposal(prepare(user)['proposal'])
    template['version'] = 'changed-while-queued'
    assert not DeploymentJobService.run_job(started['operation']['id'])['success']
    assert DeploymentJob.query.count() == 1


def test_installer_rejects_rendered_template_change_before_creating_job(setup):
    user, _, _ = setup
    result = DeploymentJobService.install_template(
        'nginx', 'demo-app', user_id=user.id, expected_template_digest='stale')
    assert not result['success']
    assert 'changed' in result['error']
    assert DeploymentJob.query.count() == 0


@pytest.mark.parametrize('outcome', [{'success': False}, {'ok': False}])
def test_failed_handler_result_cannot_complete_a_recipe_step(setup, outcome):
    from types import SimpleNamespace
    from app.services.recipe_execution_service import RecipeStepRegistry
    RecipeStepRegistry.register('verify', 'test.failure', lambda context: outcome, replace=True)
    with pytest.raises(RuntimeError, match='reported failure'):
        RecipeStepRegistry.execute(SimpleNamespace(step={'capability': 'verify:test.failure'}))


def test_execute_requires_confirmation_and_admin(setup):
    user, _, queued = setup
    proposal = prepare(user)['proposal']
    descriptor = ai_tool_registry.get('core__execute_deployment_proposal')
    assert descriptor.is_write and descriptor.admin_only
    assert not descriptor.allowed_for(make_user(db, role='viewer'))
    assert not descriptor.allowed_for(make_user(db, role='developer'))
    result = ai_service._make_write_wrapper(descriptor, user, None)(proposal=proposal)
    assert 'confirmation' in result
    assert not queued


def test_confirmation_displays_signed_preview_and_denial_does_not_launch(setup):
    import threading
    from app.models.ai import AiConversation, AiPendingAction
    user, _, queued = setup
    proposal = prepare(user)
    conversation = AiConversation(user_id=user.id)
    db.session.add(conversation)
    db.session.commit()
    frames = []

    def emit(event, payload):
        frames.append(payload)
        gate.resolve(payload['action_token'], 'deny')

    gate = ai_service.ConfirmationGate(conversation.id, user.id, emit, threading.Event(), 1)
    decision, token = gate.request_confirmation(
        ai_tool_registry.get('core__execute_deployment_proposal'), {'proposal': proposal['proposal']})
    assert decision == 'deny'
    assert frames[0]['display_params'] == proposal['preview']
    assert db.session.get(AiPendingAction, token).params == {'proposal': proposal['proposal']}
    assert not queued


def test_replay_returns_same_persistent_operation(setup):
    user, _, queued = setup
    proposal = prepare(user)['proposal']
    with caller(user):
        first = ops.execute_deployment_proposal(proposal)
        second = ops.execute_deployment_proposal(proposal)
    assert first['operation'] == second['operation']
    assert first['status'] == 'pending'
    assert not first['verified']
    assert DeploymentJob.query.count() == 1
    assert queued == [first['operation']['id']]
    # Reconnect uses the persisted UUID, even with a fresh SQLAlchemy identity map.
    db.session.expire_all()
    with caller(user):
        assert ops.execute_deployment_proposal(proposal)['operation'] == first['operation']


def test_recipe_runs_real_steps_and_preserves_verification_evidence(setup, monkeypatch):
    user, _, _ = setup
    from app.services import container_status_service
    installations = []

    def install(**kwargs):
        installations.append(kwargs)
        app = make_application(db, name=kwargs['app_name'], user_id=user.id)
        job = DeploymentJob(id=kwargs['job_id'], kind='template_install', status='succeeded',
                            requested_by=user.id, app_id=app.id)
        db.session.add(job)
        db.session.commit()
        return {'success': True, 'job_id': job.id}

    monkeypatch.setattr(DeploymentJobService, 'install_template', install)
    monkeypatch.setattr(container_status_service, 'get_app_status', lambda *a, **kw: {
        'status': 'running:healthy', 'total': 1,
        'containers': [{'name': 'web', 'state': 'running', 'health': 'none'}]})
    with caller(user):
        proposal = prepare(user)['proposal']
        started = ops.execute_deployment_proposal(proposal)
        job_id = started['operation']['id']
        result = DeploymentJobService.run_job(job_id)
        observed = ops.get_deployment_operation(job_id)
    assert result['success']
    assert observed['status'] == 'succeeded'
    assert observed['verified']
    assert observed['evidence']['verify']['runtime_verified']
    assert not observed['evidence']['verify']['application_health_verified']
    assert len(installations) == 1
    assert observed['app_id'] == observed['evidence']['install']['app_id']


def test_worker_rechecks_admin_after_queueing(setup):
    user, _, _ = setup
    with caller(user):
        started = ops.execute_deployment_proposal(prepare(user)['proposal'])
    user.role = 'viewer'
    db.session.commit()
    result = DeploymentJobService.run_job(started['operation']['id'])
    assert not result['success']
    assert 'administrator' in result['error']


def test_failed_verification_resumes_without_reinstall(setup, monkeypatch):
    user, _, _ = setup
    from app.services import recipe_builtin_steps
    from app.services.recipe_execution_service import RecipeStepRegistry
    calls = []

    def install(context):
        calls.append('install')
        return {'app_id': 123}

    def fail(context):
        raise RuntimeError('health check failed')

    with caller(user):
        started = ops.execute_deployment_proposal(prepare(user)['proposal'])
    RecipeStepRegistry.register('apply', 'template.install', install, replace=True)
    RecipeStepRegistry.register('verify', 'application.health', fail, replace=True)
    job_id = started['operation']['id']
    assert not DeploymentJobService.run_job(job_id)['success']
    RecipeStepRegistry.register('verify', 'application.health', lambda c: {'runtime_verified': True}, replace=True)
    try:
        assert DeploymentJobService.retry_job(job_id, user_id=user.id)['resumed']
        assert DeploymentJobService.run_job(job_id)['success']
        assert calls == ['install']
    finally:
        recipe_builtin_steps.register_steps()


def test_catalog_reports_unimplemented_recipe_handlers(setup, monkeypatch):
    user, _, _ = setup
    from app.services import recipe_registry_service
    monkeypatch.setattr(recipe_registry_service, 'list_catalog', lambda: [
        {'slug': 'unsupported', 'name': 'Unsupported', 'capabilities': ['apply:missing']},
        {'slug': 'template', 'name': 'Template', 'capabilities': ['apply:template.install']},
    ])
    with caller(user):
        entries = ops.list_deployment_recipes()['recipes']
    assert not entries[0]['supported']
    assert entries[0]['unsupported_capabilities'] == ['apply:missing']
    assert entries[1]['supported']


def test_operation_log_cursor_is_bounded_and_redacted(setup):
    user, _, _ = setup
    from app.models.deployment_job import DeploymentJobLog
    with caller(user):
        started = ops.execute_deployment_proposal(prepare(user)['proposal'])
    job_id = started['operation']['id']
    for index in range(12):
        db.session.add(DeploymentJobLog(job_id=job_id, level='info', message=f'password=private-{index}'))
    db.session.commit()
    wrapper = ai_service._make_read_wrapper(ai_tool_registry.get('core__get_deployment_operation'), user)
    first = wrapper(job_id=job_id)
    assert len(first['logs']) == 10
    assert 'private-' not in str(first)
    second = wrapper(job_id=job_id, after_log_id=first['next_log_id'])
    assert len(second['logs']) == 2
