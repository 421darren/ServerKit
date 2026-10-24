"""Generic preview transaction: validate, journal, build, gate, publish; compensate failures."""
import uuid
from app import db
from app.models import Domain
from app.models.application_preview import ApplicationPreview
from app.services.git_service import GitService
from app.services.nginx_service import NginxService
from . import runtime, source
from .plan import PreviewError, validate, identity, workspace


def check_domain(preview):
    domain = preview.domain.lower()
    if Domain.query_active().filter(db.func.lower(Domain.name) == domain).first():
        raise PreviewError('Preview domain is already assigned to an application.')
    if ApplicationPreview.query.filter(
        ApplicationPreview.id != preview.id,
        db.func.lower(ApplicationPreview.domain) == domain,
        ApplicationPreview.status != 'destroyed',
    ).first():
        raise PreviewError('Preview domain is already assigned to another preview.')
    owned = preview.get_runtime_state().get('token')
    own_name = identity(preview.id, owned) if owned else None
    for site in NginxService.list_sites():
        if site['name'] != own_name and domain in [d.lower() for d in site.get('domains', [])]:
            raise PreviewError('Preview domain is already configured in nginx.')


def provision(app, preview, settings):
    config = GitService.get_app_config(app.id)
    request_token = preview.request_token
    try:
        validate(app, preview, settings, config)
        check_domain(preview)
        # Stop/recreate semantics are deliberate: cleanup must finish before a
        # new attempt. We never lose ownership of an abandoned generation.
        runtime.cleanup(preview)
        state = {'token': uuid.uuid4().hex}
        runtime.save(preview, state)
        target = workspace(runtime.ROOT, preview.id, state['token'])
        target.parent.mkdir(parents=True, exist_ok=True)
        name = identity(preview.id, state['token'])
        state['source'] = True
        runtime.save(preview, state)
        source.prepare(app, preview, target, config['repo_url'])
        state['image'] = True
        runtime.save(preview, state)
        source.build(app, preview, target, name + ':preview')
        runtime.start(app, preview, state)
        db.session.refresh(preview, ['request_token', 'requested_action'])
        db.session.refresh(app, ['deleted_at'])
        if app.deleted_at or preview.request_token != request_token or preview.requested_action == 'destroy':
            raise PreviewError('Preview request was superseded or its application was deleted.')
        runtime.publish(preview, state)
        preview.error_message = None
        return {'ok': True, 'container_ids': [state['container_id']]}
    except Exception as exc:
        # Only controlled diagnostics go to the browser; host errors may carry
        # credentials or environment values. The journal survives cleanup errors.
        error = str(exc) if isinstance(exc, PreviewError) else 'Preview provisioning failed.'
        try:
            runtime.cleanup(preview)
        except Exception:
            error += ' Cleanup is incomplete; retry deletion before deploying again.'
        preview.error_message = error
        db.session.commit()
        return {'ok': False, 'container_ids': [], 'error': error}
