# Bucket: PER-APP. Reads gate on can_access_app; changes gate on
# can_edit_app.
"""A/B slot deploys. Mounted under ``/api/v1/apps``.

  GET  /<app_id>/slots               — slots, active slot, eligibility + reasons
  PUT  /<app_id>/slots               — {enabled}: opt in (adopts the current
                                       container as slot a, no restart) or out
  POST /<app_id>/slots/switch-back   — make the standby live again (a rollback
                                       to the release it holds: seconds while
                                       it is warm)
  GET  /<app_id>/slots/compose-split — preview moving stateful compose services
                                       into the shared <name>-data project
  POST /<app_id>/slots/compose-split — {confirm: true}: do it (one announced
                                       outage; the data stays on its volumes)
  POST /<app_id>/slots/restore-db    — {deployment_id}: restore the database
                                       snapshot taken before that deployment's
                                       release ran. Destroys later writes; an
                                       explicit second step after a rollback.
"""
from flask import Blueprint, jsonify

from app.exceptions import ValidationError
from app.middleware.rbac import developer_required, get_current_user, viewer_required
from app.services.slot_deploy_service import SlotDeployService
from app.api._access import require_app
from app.api._request import json_object

app_slots_bp = Blueprint('app_slots', __name__)


@app_slots_bp.route('/<int:app_id>/slots', methods=['GET'])
@viewer_required
def get_slots(app_id):
    app = require_app(app_id, conceal=True)
    return jsonify(SlotDeployService.status(app))


@app_slots_bp.route('/<int:app_id>/slots', methods=['PUT'])
@developer_required
def set_slots(app_id):
    app = require_app(app_id, write=True, conceal=True)
    data = json_object(optional=True)
    enabled = data.get('enabled')
    if not isinstance(enabled, bool):
        raise ValidationError("'enabled' must be true or false")
    result = SlotDeployService.set_enabled(app, enabled)
    if not result.get('success'):
        return jsonify(result), 409
    return jsonify(result)


@app_slots_bp.route('/<int:app_id>/slots/switch-back', methods=['POST'])
@developer_required
def switch_back(app_id):
    app = require_app(app_id, write=True, conceal=True)
    result = SlotDeployService.switch_back(app, user_id=get_current_user().id)
    if not result.get('success'):
        return jsonify(result), 409
    return jsonify(result)


@app_slots_bp.route('/<int:app_id>/slots/restore-db', methods=['POST'])
@developer_required
def restore_db(app_id):
    app = require_app(app_id, write=True, conceal=True)
    data = json_object(optional=True)
    deployment_id = data.get('deployment_id')
    if not isinstance(deployment_id, int) or isinstance(deployment_id, bool):
        raise ValidationError("'deployment_id' is required")
    result = SlotDeployService.restore_databases(app, deployment_id)
    if not result.get('success'):
        return jsonify(result), 409
    return jsonify(result)


@app_slots_bp.route('/<int:app_id>/slots/compose-split', methods=['GET'])
@viewer_required
def compose_split_preview(app_id):
    app = require_app(app_id, conceal=True)
    result = SlotDeployService.compose_split_preview(app)
    if not result.get('success'):
        return jsonify(result), 409
    return jsonify(result)


@app_slots_bp.route('/<int:app_id>/slots/compose-split', methods=['POST'])
@developer_required
def compose_split_apply(app_id):
    app = require_app(app_id, write=True, conceal=True)
    data = json_object(optional=True)
    if data.get('confirm') is not True:
        raise ValidationError("Moving the stateful services stops the service once; send "
                              "{'confirm': true} after reading the preview")
    result = SlotDeployService.compose_split_apply(app)
    if not result.get('success'):
        return jsonify(result), 409
    return jsonify(result)
