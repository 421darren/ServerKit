"""Small, closed Recipe capabilities for approved template deployments.

Reuses the installer and live status collector. A resumed recipe never blindly
replays an interrupted installation; it reconnects to its deterministic child job.
"""
import time
import uuid

from app import db


def _authorized(context):
    from app.models.user import User
    user = db.session.get(User, context.job.requested_by, populate_existing=True)
    if user is None or not user.is_active or not user.is_admin:
        raise PermissionError('Deployment requires an active administrator.')
    return user


def install_template(context):
    from app.models import Application
    from app.models.deployment_job import DeploymentJob
    from app.services.deployment_job_service import DeploymentJobService
    from app.services.ai_operations import _template, _digest, _public_variables, _target
    from app.utils.slug import validate_app_name

    user = _authorized(context)
    params = context.step.get('params') or {}
    app_name = params.get('app_name', '')
    valid, error = validate_app_name(app_name, min_length=3)
    if not valid:
        raise ValueError(error)
    target = _target(params.get('server_id'))
    template = _template(params.get('template_id'))
    # Compare the effective template too: auto_domain may modify its top-level flag.
    if _digest(template) != params.get('digest'):
        raise ValueError('Template changed after approval. Prepare a new proposal.')
    effective = {**template, 'auto_domain': True} if params.get('auto_domain') else template
    variables = _public_variables(template, params.get('variables') or {})
    child_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f'serverkit:{context.job.id}:{context.step["id"]}'))
    child = db.session.get(DeploymentJob, child_id)
    if child is None:
        if not target['online']:
            raise ValueError('Target server is offline.')
        result = DeploymentJobService.install_template(
            template_id=params['template_id'], app_name=app_name,
            user_variables=variables, user_id=user.id,
            server_id=params['server_id'], auto_domain=params.get('auto_domain', False),
            wait=True, job_id=child_id, expected_template_digest=_digest(effective))
        child = db.session.get(DeploymentJob, child_id)
        if child is None:
            raise RuntimeError(result.get('error') or 'Installation could not start.')
    if child.status != 'succeeded':
        raise RuntimeError(f'Installation {child.id} is {child.status}. Inspect it in Operations; it will not be replayed.')
    app = Application.query_active().filter_by(id=child.app_id).first()
    if app is None:
        raise RuntimeError('Installed application no longer exists.')
    app.project_id = context.project.id
    app.environment_id = getattr(context.environment, 'id', None)
    app.workspace_id = context.project.workspace_id
    context.job.app_id = app.id
    context.job.target_server_id = app.server_id
    db.session.commit()
    # Never copy generated variables, compose content or credentials into tool evidence.
    result = child.get_result() or {}
    domain = result.get('auto_domain') or {}
    return {'app_id': app.id, 'name': app.name, 'job_id': child.id,
            'server_id': app.server_id or 'local', 'port': app.port,
            'url': domain.get('url') if domain.get('success') else None}


def verify_application(context):
    from app.models import Application
    from app.services.container_status_service import get_app_status
    _authorized(context)
    step_id = (context.step.get('params') or {}).get('install_step')
    installed = (context.completed.get(step_id) or {}).get('result') or {}
    app = Application.query_active().filter_by(id=installed.get('app_id')).first()
    if app is None or app.project_id != context.project.id:
        raise ValueError('Verification must reference an application installed by this recipe.')
    # Bounded wait is in the persistent job worker, never the chat request.
    deadline = time.monotonic() + 60
    while True:
        _authorized(context)
        result = get_app_status(app.id, use_cache=False)
        if result.get('status') == 'running:healthy' and result.get('total', 0) > 0:
            containers = result.get('containers') or []
            return {'app_id': app.id, 'runtime_verified': True,
                    'application_health_verified': bool(containers) and
                    all(c.get('health') == 'healthy' for c in containers),
                    'scope': 'Running containers and configured Docker health checks; no HTTP/login test.',
                    'containers': containers}
        if time.monotonic() >= deadline:
            raise RuntimeError('Container verification did not pass within 60 seconds: ' + str(result.get('status')))
        time.sleep(3)


def register_steps():
    from app.services.recipe_execution_service import RecipeStepRegistry
    RecipeStepRegistry.register('apply', 'template.install', install_template, replace=True)
    RecipeStepRegistry.register('verify', 'application.health', verify_application, replace=True)
