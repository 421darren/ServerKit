"""Application deletion must not orphan preview-owned host resources."""
from app.models.application_preview import ApplicationPreview


def cleanup_application(app_id):
    from app.services.preview_service import PreviewService
    rows = ApplicationPreview.query.filter_by(application_id=app_id).all()
    failed = []
    for row in rows:
        if row.status != 'destroyed' or row.get_runtime_state():
            result = PreviewService.destroy_preview(row.id)
            if result.get('error'):
                failed.append(row.id)
    return {'success': not failed, 'failed_preview_ids': failed}
