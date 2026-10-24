"""Agent-facing deployment workflows backed by Recipes and DeploymentJobs.

Proposals contain only public inputs, are signed, caller-bound and expire.
Their UUID is the deployment primary key: replay reconnects to the same run.
No shell, provider credential or arbitrary URL is exposed as an AI tool.
"""
import hashlib
import json
import re
import threading
import uuid
from functools import wraps

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import db
from app.exceptions import ValidationError

_launch_lock = threading.RLock()
PROPOSAL_TTL = 900


def _caller():
    from app.services.ai_tools_builtin import _caller as caller
    return caller(admin=True)


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='ai-deployment-v1')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _template(template_id):
    from app.services.template_service import TemplateService
    if not isinstance(template_id, str) or not re.fullmatch(r'[\w-]{1,100}', template_id):
        raise ValidationError('Choose a template ID from the catalog.')
    result = TemplateService.get_template(template_id)
    if not result.get('success'):
        raise ValidationError('Template unavailable. Refresh the catalog.')
    return result['template']


def _variables(template):
    raw = template.get('variables') or {}
    return ({v['name']: v for v in raw if isinstance(v, dict) and 'name' in v}
            if isinstance(raw, list) else raw)


def _public_variables(template, variables):
    from app.utils.sensitive_data_filter import SENSITIVE_KEY_PARTS
    if not isinstance(variables, dict) or len(json.dumps(variables)) > 2048:
        raise ValidationError('Supply at most 2048 characters of public template variables.')
    specs = _variables(template)
    for key, value in variables.items():
        spec = specs.get(key)
        if not isinstance(spec, dict):
            raise ValidationError('Unknown template variable.')
        if (spec.get('type') in ('password', 'random', 'uuid') or spec.get('secret')
                or any(part.lower() in key.lower() for part in SENSITIVE_KEY_PARTS)):
            raise ValidationError('Use the deployment form for credentials; never put secrets in chat.')
        if not isinstance(value, (str, int, float, bool)):
            raise ValidationError('Template variables must be scalar values.')
    return variables


def _target(server_id):
    from app.models.server import Server
    from app.services.agent_registry import agent_registry
    if server_id == 'local':
        return {'id': 'local', 'name': 'Panel host', 'online': True}
    server = db.session.get(Server, server_id) if isinstance(server_id, str) else None
    if server is None:
        raise ValidationError('Select an existing server ID or explicitly use local.')
    return {'id': server.id, 'name': server.name,
            'online': agent_registry.is_agent_connected(server.id)}


def _proposal(data):
    user = _caller()
    return _serializer().dumps({**data, 'user_id': user.id,
                                'auth_version': user.auth_version, 'id': str(uuid.uuid4())})


def _proposal_result(data):
    from app.services.ai_management import settings
    result = {'success': True, 'preview': data['preview'],
              'expires_in_seconds': PROPOSAL_TTL, 'proposal': _proposal(data)}
    # Prompture truncates serialized tool results. Never hand the model a
    # partial approval token, even when an operator lowers the output budget.
    if len(json.dumps(result)) > settings()['max_tool_result_length']:
        raise ValidationError('Preview exceeds the AI tool output limit. Use the deployment form or increase that limit.')
    return result


def decode_proposal(proposal, user):
    if not isinstance(proposal, str) or len(proposal) > 12000:
        raise ValidationError('Invalid deployment proposal.')
    try:
        data = _serializer().loads(proposal, max_age=PROPOSAL_TTL)
    except (BadSignature, SignatureExpired):
        raise ValidationError('Proposal expired or changed. Prepare a new preview.') from None
    if user is None or data.get('user_id') != user.id or data.get('auth_version') != user.auth_version:
        raise PermissionError('This proposal belongs to a different session owner.')
    return data


def proposal_details(proposal, user):
    """Server-derived approval text; the model cannot substitute a summary."""
    data = decode_proposal(proposal, user)
    return data['preview']


def list_deployment_templates(search: str = '', offset: int = 0) -> dict:
    """Find installable application templates. Browse before preparing a deployment.

    Args:
        search: Application name or category to search for.
        offset: Pagination offset; ten entries are returned at a time.
    """
    _caller()
    from app.services.template_service import TemplateService
    rows = TemplateService.list_all_templates(search=search[:100])
    offset = max(0, int(offset))
    fields = ('id', 'name', 'description', 'version', 'kind')
    return {'templates': [{k: str(r.get(k, ''))[:180] for k in fields}
                          for r in rows[offset:offset + 10]],
            'total': len(rows), 'next_offset': offset + 10 if offset + 10 < len(rows) else None}


def get_deployment_template(template_id: str) -> dict:
    """Inspect a template's public inputs before preparing a proposal.

    Args:
        template_id: ID returned by list_deployment_templates.
    """
    _caller()
    template = _template(template_id)
    fields = ('description', 'type', 'required', 'options')
    return {'id': template_id, 'name': template.get('name'),
            'variables': [{'name': name, **{k: spec.get(k) for k in fields}}
                          for name, spec in _variables(template).items()],
            'credentials': 'Generated credentials stay on the server. Use the deployment form for secret inputs.'}


def inspect_deployment_target(server_id: str) -> dict:
    """Inspect connectivity and reported capabilities of a deployment target.

    Args:
        server_id: Fleet server ID, or local for the panel host.
    """
    _caller()
    target = _target(server_id)
    if server_id == 'local':
        from app.services.docker_service import DockerService
        target['docker_installed'] = DockerService.is_docker_installed()
    else:
        from app.services.agent_registry import agent_registry
        target['capabilities'] = agent_registry.get_capabilities(server_id)
    return target


def prepare_template_deployment(template_id: str, app_name: str, server_id: str,
                                variables: dict = None, auto_domain: bool = False) -> dict:
    """Preview a new template deployment without installing anything; returns a signed proposal.

    Args:
        template_id: Catalog template ID.
        app_name: Unique service name, at least three characters.
        server_id: Explicit fleet server ID or local for the panel host.
        variables: Public template inputs only. Never supply credentials in chat.
        auto_domain: Whether to request automatic domain publication.
    """
    _caller()
    from app.models import Application
    from app.utils.slug import validate_app_name
    from app.services.template_service import TemplateService
    valid, error = validate_app_name(app_name, min_length=3)
    if not valid:
        raise ValidationError(error)
    target = _target(server_id)
    if not target['online']:
        raise ValidationError('Target server is offline.')
    if Application.query.filter_by(name=app_name, server_id=None if server_id == 'local' else server_id).first():
        raise ValidationError('That application name is already reserved on this server.')
    template = _template(template_id)
    if template.get('kind', 'compose') != 'compose':
        raise ValidationError('Use the repository deployment form for this template kind.')
    variables = _public_variables(template, variables or {})
    if auto_domain and server_id != 'local':
        raise ValidationError('Automatic domain publication is only supported on the panel host.')
    # Render to validate required inputs and provider preflight; never expose generated secrets.
    result = TemplateService.build_install_plan(template_id, app_name, variables,
                                               server_id=None if server_id == 'local' else server_id,
                                               auto_domain=auto_domain)
    if not result.get('success'):
        return {'success': False, 'error': result.get('error', 'Template preflight failed')}
    if _digest(result['template']) != _digest({**template, 'auto_domain': True} if auto_domain else template):
        raise ValidationError('Template changed during preview. Prepare it again.')
    preview = {'action': 'Install template and verify container state',
               'template': template_id, 'application': app_name, 'server': target,
               'variables': variables,
               'auto_domain': bool(auto_domain or template.get('auto_domain')) and server_id == 'local',
               'ports': 'Allocated when execution starts',
               'verification': 'Running containers and configured Docker health checks; not an HTTP or login test.'}
    return _proposal_result({'kind': 'template', 'template_id': template_id,
                                   'app_name': app_name, 'server_id': server_id,
                                   'variables': variables, 'auto_domain': bool(auto_domain),
                                   'digest': _digest(template), 'preview': preview})


def list_deployment_recipes() -> dict:
    """List recipe availability, including missing handlers. Unsupported recipes cannot run."""
    _caller()
    from app.services import recipe_registry_service
    from app.services.recipe_execution_service import RecipeExecutionService, RecipeStepRegistry
    RecipeExecutionService.register_jobs()
    rows = []
    for entry in recipe_registry_service.list_catalog():
        missing = [c for c in entry.get('capabilities', []) if not RecipeStepRegistry.supports(c)]
        rows.append({'slug': entry['slug'], 'name': entry['name'],
                     'supported': not missing, 'unsupported_capabilities': missing})
    return {'recipes': rows}


def prepare_recipe_deployment(registry_slug: str, project_id: int) -> dict:
    """Preview a catalog recipe for an existing project. Secret handoffs stay in Operations.

    Args:
        registry_slug: Slug returned by list_deployment_recipes.
        project_id: Existing ServerKit project ID.
    """
    _caller()
    from app.models.project import Project
    from app.services import recipe_registry_service
    from app.services.manifest_spec_service import ManifestSpecService
    from app.services.manifest_apply_service import ManifestApplyService
    from app.services.recipe_execution_service import RecipeExecutionService
    project = db.session.get(Project, project_id)
    if project is None:
        raise ValidationError('Select an existing project.')
    text = recipe_registry_service.get_manifest_text(registry_slug)
    normalized = ManifestSpecService.normalize_text(text)
    RecipeExecutionService.register_jobs()
    missing = RecipeExecutionService.unsupported_capabilities(normalized)
    plan = ManifestApplyService.plan(project, normalized)
    if missing or plan.get('blockers'):
        return {'success': False, 'unsupported_capabilities': missing,
                'blockers': plan.get('blockers', [])}
    preview = {'action': 'Run catalog recipe', 'recipe': registry_slug,
               'project_id': project.id, 'project': project.name,
               'changes': [s.get('description') for s in plan.get('steps', [])],
               'steps': [s.get('title') for s in normalized.get('configure', []) + normalized.get('verify', [])],
               'handoffs': 'Supply requested credentials directly in Operations, never in chat.'}
    return _proposal_result({'kind': 'recipe', 'registry_slug': registry_slug,
                                   'project_id': project_id, 'digest': _digest(normalized),
                                   'preview': preview})


def execute_deployment_proposal(proposal: str) -> dict:
    """Start an approved deployment in Operations. Reusing the proposal returns the same run.

    Args:
        proposal: Exact signed proposal returned by a prepare tool. Requires human approval.
    """
    user = _caller()
    data = decode_proposal(proposal, user)
    from app.models.deployment_job import DeploymentJob
    from app.services.recipe_execution_service import RecipeExecutionService
    from app.services.manifest_spec_service import ManifestSpecService
    from app.models.project import Project
    with _launch_lock:
        existing = db.session.get(DeploymentJob, data['id'])
        if existing:
            if existing.requested_by != user.id:
                raise PermissionError('Operation belongs to a different user.')
            return get_deployment_operation(existing.id)
        if data['kind'] == 'template':
            if _digest(_template(data['template_id'])) != data['digest']:
                raise ValidationError('Template changed. Prepare and approve a new preview.')
            if not _target(data['server_id'])['online']:
                raise ValidationError('Target server is offline.')
            if data['server_id'] != 'local':
                project = RecipeExecutionService.get_or_create_project(
                    RecipeExecutionService.get_server(data['server_id']))
            else:
                from app.services.workspace_service import WorkspaceService
                workspace = WorkspaceService.ensure_default_workspace()
                project = Project.query.filter_by(workspace_id=workspace.id, slug='recipes').first()
                if project is None:
                    project = Project(workspace_id=workspace.id, slug='recipes', name='Recipes')
                    db.session.add(project)
                    db.session.flush()
            normalized = ManifestSpecService.normalize({
                'version': 1, 'capabilities': ['apply:template.install', 'verify:application.health'],
                'configure': [{'id': 'install', 'type': 'apply', 'kind': 'template.install',
                               'title': 'Install ' + data['app_name'], 'params': data}],
                'verify': [{'id': 'verify', 'kind': 'application.health', 'dependsOn': ['install'],
                            'title': 'Verify running containers', 'params': {'install_step': 'install'}}],
            })
        else:
            from app.services import recipe_registry_service
            normalized = ManifestSpecService.normalize_text(
                recipe_registry_service.get_manifest_text(data['registry_slug']))
            if _digest(normalized) != data['digest']:
                raise ValidationError('Recipe changed. Prepare and approve a new preview.')
            project = db.session.get(Project, data['project_id'])
            if project is None:
                raise ValidationError('Project no longer exists.')
        result = RecipeExecutionService.start(project, normalized, user_id=user.id,
                                               title=data['preview'].get('application') or data['registry_slug'],
                                               job_id=data['id'], server_id=data.get('server_id'))
        if not result.get('success'):
            return {'success': False, 'error': result.get('error'),
                    'unsupported_capabilities': result.get('unsupported_capabilities', [])}
        return get_deployment_operation(result['job_id'])


def get_deployment_operation(job_id: str, after_log_id: int = 0) -> dict:
    """Read a persistent deployment and a bounded log page. Queued is not deployed or healthy.

    Args:
        job_id: Deployment operation UUID returned by execute_deployment_proposal.
        after_log_id: Log cursor from the previous response; zero starts at the beginning.
    """
    _caller()
    from app.models.deployment_job import DeploymentJob, DeploymentJobLog
    job = db.session.get(DeploymentJob, job_id)
    if job is None:
        raise ValidationError('Deployment operation not found.')
    rows = DeploymentJobLog.query.filter(DeploymentJobLog.job_id == job.id,
        DeploymentJobLog.id > max(0, int(after_log_id))).order_by(DeploymentJobLog.id).limit(10).all()
    state = job.get_result() or {}
    return {'success': job.status != 'failed', 'operation': {'run_kind': 'deploy', 'id': job.id},
            'status': job.status, 'app_id': job.app_id, 'current_step': job.current_step,
            'total_steps': job.total_steps, 'error': (job.error_message or '')[:300] or None,
            'verified': bool(state.get('verified')), 'requires_action': job.status == 'waiting',
            'next_action': 'Open Operations to supply handoff inputs or retry a failed run.' if job.status in ('waiting', 'failed') else
                           'Check this operation again later. Do not launch a duplicate.' if job.status in ('pending', 'running') else
                           'Inspect verification evidence before reporting success.',
            'evidence': _operation_evidence(state),
            'logs': [{'id': r.id, 'level': r.level, 'message': r.message[:120],
                      'truncated': len(r.message) > 120} for r in rows],
            'next_log_id': rows[-1].id if rows else after_log_id}


def _operation_evidence(state):
    fields = ('app_id', 'name', 'server_id', 'port', 'url', 'runtime_verified',
              'application_health_verified', 'scope', 'job_id')
    evidence = {}
    for name, step in list(state.get('completed_steps', {}).items())[-3:]:
        result = step.get('result') or {}
        if isinstance(result, dict):
            evidence[name[:80]] = {k: (v[:180] if isinstance(v, str) else v)
                                  for k, v in result.items() if k in fields
                                  and isinstance(v, (str, int, float, bool, type(None)))}
    return evidence


def get_application_health(app_id: int) -> dict:
    """Read fresh container state. Running without a health check is not verified application health.

    Args:
        app_id: ServerKit application ID.
    """
    _caller()
    from app.models import Application
    from app.services.container_status_service import get_app_status
    app = Application.query_active().filter_by(id=app_id).first()
    if app is None:
        raise ValidationError('Application not found.')
    status = get_app_status(app.id, use_cache=False)
    containers = status.get('containers') or []
    return {'app_id': app.id, 'name': app.name, 'server_id': app.server_id or 'local',
            'runtime': status, 'application_health_verified': bool(containers) and
            all(c.get('state') == 'running' and c.get('health') == 'healthy' for c in containers),
            'verification_scope': 'Container state and configured Docker health checks only.'}


def list_deployment_projects() -> dict:
    """List projects available for a catalog recipe, including their IDs and workspace IDs."""
    _caller()
    from app.models.project import Project
    return {'projects': [{'id': p.id, 'name': p.name, 'workspace_id': p.workspace_id}
                         for p in Project.query.order_by(Project.id).limit(50).all()]}


def get_application_details(app_id: int) -> dict:
    """Inspect an application, its domains and deployment history without exposing configuration secrets.

    Args:
        app_id: ServerKit application ID.
    """
    _caller()
    from app.models import Application
    from app.models.deployment_job import DeploymentJob
    app = Application.query_active().filter_by(id=app_id).first()
    if app is None:
        raise ValidationError('Application not found.')
    jobs = DeploymentJob.query.filter_by(app_id=app.id).order_by(DeploymentJob.created_at.desc()).limit(5).all()
    return {'id': app.id, 'name': app.name, 'status': app.status,
            'server_id': app.server_id or 'local', 'project_id': app.project_id,
            'port': app.port, 'domains': [d.name for d in app.live_domains],
            'deployments': [{'id': j.id, 'status': j.status} for j in jobs]}


def get_docker_container_logs(container_id: str, tail: int = 30) -> dict:
    """Read bounded container logs on the panel host. For remote deployments use operation logs.

    Args:
        container_id: Container ID or name from list_docker_containers.
        tail: Number of recent lines, from 1 to 50.
    """
    _caller()
    from app.services.docker_service import DockerService
    if not isinstance(container_id, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}', container_id):
        raise ValidationError('Invalid container ID or name.')
    result = DockerService.get_container_logs(container_id, tail=max(1, min(50, int(tail))))
    if not result.get('success'):
        return {'success': False, 'error': 'Container logs are unavailable.'}
    return {'success': True, 'container_id': container_id, 'logs': str(result.get('logs', ''))[-3000:]}


def _tool_result(func):
    @wraps(func)
    def invoke(**kwargs):
        try:
            return func(**kwargs)
        except ValidationError as exc:
            # These are deliberate public input errors. The AI wrapper still
            # applies its normal secret/PII filter to this structured result.
            return {'success': False, 'error': str(exc)}
    return invoke


def register_tools(registry):
    reads = (list_deployment_templates, get_deployment_template, inspect_deployment_target,
             prepare_template_deployment, list_deployment_recipes, prepare_recipe_deployment,
             get_deployment_operation, get_application_health, list_deployment_projects,
             get_application_details, get_docker_container_logs)
    for func in reads:
        registry.register(name=func.__name__, func=_tool_result(func), admin_only=True,
                          rbac_feature='applications', rbac_level='read')
    registry.register(name='execute_deployment_proposal', func=_tool_result(execute_deployment_proposal),
                      admin_only=True, rbac_feature='applications', is_write=True)
