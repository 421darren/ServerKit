"""Short request reservations, separate from long-running deployment locks."""
import uuid
from app import db
from app.models.application_preview import ApplicationPreview
from app.jobs.service import JobService
from app.services.deploy_lock import deploy_lock
from .plan import PreviewError


def enqueue(app_id, pr, action='create'):
    try:
        number = int(pr.get('pr_number'))
    except (TypeError, ValueError):
        raise PreviewError('A positive PR number is required.')
    if number <= 0 or action not in ('create', 'destroy'):
        raise PreviewError('Invalid preview request.')
    # Distinct from the app deploy lock: a close can supersede an in-flight
    # build immediately instead of blocking the webhook for several minutes.
    with deploy_lock(f'preview-request-{app_id}', 'preview request'):
        row = ApplicationPreview.query.filter_by(application_id=app_id, pr_number=number).first()
        if row is None:
            row = ApplicationPreview(application_id=app_id, pr_number=number, status='queued')
            db.session.add(row)
        row.request_token = uuid.uuid4().hex
        row.requested_action = action
        db.session.commit()
        return JobService.enqueue('preview.' + action, {
            'application_id': app_id, 'preview_id': row.id, 'pr': pr,
            'request_token': row.request_token,
        }, max_attempts=1, owner_type='application', owner_id=str(app_id))


def current(payload):
    if not payload.get('request_token'):
        return True  # compatibility with older queued jobs
    row = db.session.get(ApplicationPreview, payload.get('preview_id'))
    if not row:
        return False
    db.session.refresh(row, ['request_token'])
    return row.request_token == payload['request_token']


def validate_request(app, data):
    from types import SimpleNamespace
    from app.services.preview_service import PreviewService
    from app.services.git_service import GitService
    from .plan import validate
    settings = PreviewService.get_settings(app.id)
    if not settings.enabled:
        raise PreviewError('Enable previews before deploying.')
    try:
        number = int(data.get('pr_number'))
    except (TypeError, ValueError):
        raise PreviewError('A positive PR number is required.')
    candidate = SimpleNamespace(pr_number=number, branch=data.get('branch'),
                                commit_sha=data.get('commit_sha'),
                                domain=PreviewService._domain_for(app, settings, number, data.get('branch')))
    validate(app, candidate, settings, GitService.get_app_config(app.id))
    return {'pr_number': number, 'branch': candidate.branch,
            'commit_sha': candidate.commit_sha, 'pr_title': data.get('pr_title')}
