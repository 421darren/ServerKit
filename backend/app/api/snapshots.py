# Bucket: PER-APP. Snapshot reads (list/get/diff) require app
# access (can_access_app); restore requires write access (can_edit_app) on top
# of the panel-wide @developer_required.
"""
Deployment config snapshot API.

Mounted by the app factory at ``/api/v1/apps``. Exposes the immutable
configuration snapshots captured before each deployment: list, fetch, diff and
restore. Diffs and listings never leak secret values — env values are already
masked at snapshot time.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.middleware.rbac import developer_required, get_current_user
from app.models.deployment_snapshot import DeploymentSnapshot
from app.services.configuration_service import ConfigurationService
from app.exceptions import not_found
from app.api._access import require_app

snapshots_bp = Blueprint('snapshots', __name__)


def _get_snapshot_or_404(app_id, snap_id):
    """Return (snapshot, None) or (None, error_response). Scoped to the app."""
    snap = DeploymentSnapshot.query.filter_by(
        id=snap_id, application_id=app_id
    ).first()
    if not snap:
        raise not_found('config_checkpoint')
    return snap, None


# "Config Checkpoint" is the user-facing name for a deployment config snapshot
# (§8 decision: rename in the UI; keep /snapshots working). Every route below is
# also reachable under /config-checkpoints so the API matches the new wording.
@snapshots_bp.route('/<int:app_id>/snapshots', methods=['GET'])
@snapshots_bp.route('/<int:app_id>/config-checkpoints', methods=['GET'])
@jwt_required()
def list_snapshots(app_id):
    """List config snapshots for an app, newest first."""
    app = require_app(app_id)

    try:
        limit = min(int(request.args.get('limit', 50)), 200)
    except (TypeError, ValueError):
        limit = 50

    snapshots = (
        DeploymentSnapshot.query.filter_by(application_id=app_id)
        .order_by(DeploymentSnapshot.created_at.desc(), DeploymentSnapshot.id.desc())
        .limit(limit)
        .all()
    )
    # List view omits the full config payload to keep responses light.
    return jsonify({
        'snapshots': [s.to_dict(include_config=False) for s in snapshots]
    }), 200


@snapshots_bp.route('/<int:app_id>/snapshots/<int:snap_id>', methods=['GET'])
@snapshots_bp.route('/<int:app_id>/config-checkpoints/<int:snap_id>', methods=['GET'])
@jwt_required()
def get_snapshot(app_id, snap_id):
    """Fetch a single snapshot, including its resolved config."""
    require_app(app_id)
    snap, err = _get_snapshot_or_404(app_id, snap_id)
    if err:
        return err
    return jsonify({'snapshot': snap.to_dict(include_config=True)}), 200


@snapshots_bp.route('/<int:app_id>/snapshots/<int:snap_id>/diff', methods=['GET'])
@snapshots_bp.route('/<int:app_id>/config-checkpoints/<int:snap_id>/diff', methods=['GET'])
@jwt_required()
def diff_snapshot(app_id, snap_id):
    """Diff a snapshot against another (default: the previous snapshot).

    Query param ``against`` accepts another snapshot id or the literal
    ``previous`` (default).
    """
    require_app(app_id)
    snap, err = _get_snapshot_or_404(app_id, snap_id)
    if err:
        return err

    against = request.args.get('against', 'previous')

    if against == 'previous' or against in (None, ''):
        other = (
            DeploymentSnapshot.query.filter(
                DeploymentSnapshot.application_id == app_id,
                DeploymentSnapshot.created_at < snap.created_at,
            )
            .order_by(DeploymentSnapshot.created_at.desc(), DeploymentSnapshot.id.desc())
            .first()
        )
    else:
        try:
            other_id = int(against)
        except (TypeError, ValueError):
            return jsonify({'error': "Invalid 'against' parameter"}), 400
        other, e404 = _get_snapshot_or_404(app_id, other_id)
        if e404:
            return e404

    old_config = other.get_config() if other else {}
    new_config = snap.get_config()
    diff = ConfigurationService.diff_configs(old_config, new_config)

    return jsonify({
        'snapshot_id': snap.id,
        'against_id': other.id if other else None,
        'diff': diff,
        'summary': ConfigurationService.summarize_diff(diff),
        'has_changes': ConfigurationService.has_changes(diff),
    }), 200


@snapshots_bp.route('/<int:app_id>/snapshots/<int:snap_id>/restore', methods=['POST'])
@snapshots_bp.route('/<int:app_id>/config-checkpoints/<int:snap_id>/restore', methods=['POST'])
@developer_required
def restore_snapshot(app_id, snap_id):
    """Restore a snapshot's config (env/domains) and trigger a redeploy."""
    require_app(app_id, write=True)
    snap, err = _get_snapshot_or_404(app_id, snap_id)
    if err:
        return err

    user = get_current_user()
    user_id = user.id if user else get_jwt_identity()

    result = ConfigurationService.restore_snapshot(snap.id, user_id=user_id)
    status = 200 if result.get('success') else 400
    return jsonify(result), status
