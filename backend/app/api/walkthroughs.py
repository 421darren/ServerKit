"""Self-scoped guided walkthrough progress API."""

from flask import Blueprint, jsonify

from app.middleware.rbac import admin_required, get_current_user, require_role, viewer_required
from app.services.walkthrough_definition_service import (
    WalkthroughDefinitionError,
    WalkthroughDefinitionService,
)
from app.services.walkthrough_service import (
    WalkthroughService,
    WalkthroughStateError,
)
from app.api._request import json_object


walkthroughs_bp = Blueprint('walkthroughs', __name__)


@walkthroughs_bp.route('/state', methods=['GET'])
@viewer_required
def get_walkthrough_state():
    user = get_current_user()
    return jsonify({'state': WalkthroughService.get_state(user.id)}), 200


@walkthroughs_bp.route('/state', methods=['PUT'])
@require_role('admin', 'developer', 'viewer')
def update_walkthrough_state():
    user = get_current_user()
    data = json_object(optional=True)
    try:
        state = WalkthroughService.save_state(user.id, data.get('state', data))
    except WalkthroughStateError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify({'success': True, 'state': state}), 200


@walkthroughs_bp.route('/definitions', methods=['GET'])
@viewer_required
def get_walkthrough_definitions():
    return jsonify({
        'definitions': WalkthroughDefinitionService.get_definitions(),
    }), 200


@walkthroughs_bp.route('/definitions', methods=['PUT'])
@admin_required
def update_walkthrough_definitions():
    data = json_object(optional=True)
    try:
        definitions = WalkthroughDefinitionService.save_definitions(
            data.get('definitions', data),
        )
    except WalkthroughDefinitionError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify({'success': True, 'definitions': definitions}), 200
