"""Malware scanner API — ClamAV status/install/definitions, file/directory
scans, job-backed app-docroot scans (YARA + ClamAV), quarantine, and YARA
rule management, moved out of the host's security suite.

Routes keep their historical paths under the shared ``/api/v1/security``
url_prefix, so the frontend client is a drop-in. The scan-history log and
the notification fan-out stay core (``SecurityService``); this blueprint
carries only the scanner/quarantine surface. Host-level malware surfaces
stay admin-only. Job registration for
``security.malware_scan`` happens through the manifest's ``jobs`` key —
no import-time ``register_jobs()`` call here.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.middleware.rbac import admin_required
from app.services.security_service import SecurityService

from .clamav_service import ClamAVService
from .malware_scan_service import MalwareScanService
from .yara_scan_service import YaraScanService

clamav_bp = Blueprint('security_clamav', __name__)


# ==========================================
# CLAMAV
# ==========================================
@clamav_bp.route('/clamav/status', methods=['GET'])
@jwt_required()
def get_clamav_status():
    """Get ClamAV installation and service status."""
    status = ClamAVService.get_clamav_status()
    return jsonify(status), 200


@clamav_bp.route('/clamav/install', methods=['POST'])
@admin_required
def install_clamav():
    """Install ClamAV packages."""
    result = ClamAVService.install_clamav()
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/clamav/update', methods=['POST'])
@admin_required
def update_definitions():
    """Update ClamAV virus definitions."""
    result = ClamAVService.update_definitions()
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/clamav/start', methods=['POST'])
@admin_required
def start_clamav():
    """Start the ClamAV daemon (one-click posture fix)."""
    result = ClamAVService.start_clamav()
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/scan/file', methods=['POST'])
@admin_required
def scan_file():
    """Scan a single file for malware."""
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'File path required'}), 400

    result = ClamAVService.scan_file(data['path'])
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/scan/directory', methods=['POST'])
@admin_required
def scan_directory():
    """Start a directory scan (runs in background)."""
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Directory path required'}), 400

    recursive = data.get('recursive', True)
    result = ClamAVService.scan_directory(data['path'], recursive)
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/scan/app/<int:app_id>', methods=['POST'])
@admin_required
def scan_app(app_id):
    """Enqueue a job-backed malware scan (YARA + ClamAV) of an app's docroot."""
    job = MalwareScanService.enqueue_scan(app_id=app_id)
    return jsonify({'job_id': job.id, 'kind': job.kind,
                    'path': (job.get_payload() or {}).get('path')}), 202


@clamav_bp.route('/scan/job', methods=['POST'])
@admin_required
def scan_path_job():
    """Enqueue a job-backed malware scan of an arbitrary path."""
    data = request.get_json()
    if not data or not data.get('path'):
        return jsonify({'error': 'Path required'}), 400
    job = MalwareScanService.enqueue_scan(path=data['path'])
    return jsonify({'job_id': job.id, 'kind': job.kind, 'path': data['path']}), 202


@clamav_bp.route('/scan/status', methods=['GET'])
@jwt_required()
def get_scan_status():
    """Get current scan status."""
    status = ClamAVService.get_scan_status()
    return jsonify(status), 200


@clamav_bp.route('/scan/cancel', methods=['POST'])
@admin_required
def cancel_scan():
    """Cancel running scan."""
    result = ClamAVService.cancel_scan()
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/scan/history', methods=['GET'])
@jwt_required()
def get_scan_history():
    """Get scan history (the log itself stays core)."""
    limit = request.args.get('limit', 50, type=int)
    result = SecurityService.get_scan_history(limit)
    return jsonify(result), 200 if result['success'] else 400


# ==========================================
# QUARANTINE
# ==========================================
@clamav_bp.route('/quarantine', methods=['GET'])
@admin_required
def get_quarantined_files():
    """List quarantined files."""
    result = ClamAVService.get_quarantined_files()
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/quarantine', methods=['POST'])
@admin_required
def quarantine_file():
    """Move a file to quarantine."""
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'File path required'}), 400

    result = ClamAVService.quarantine_file(data['path'])
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/quarantine/<filename>', methods=['DELETE'])
@admin_required
def delete_quarantined_file(filename):
    """Permanently delete a quarantined file."""
    result = ClamAVService.delete_quarantined_file(filename)
    return jsonify(result), 200 if result['success'] else 400


@clamav_bp.route('/quarantine/<filename>/restore', methods=['POST'])
@admin_required
def restore_quarantined_file(filename):
    """Restore a quarantined file to its recorded original location."""
    result = ClamAVService.restore_quarantined_file(filename)
    return jsonify(result), 200 if result['success'] else 400


# ==========================================
# YARA RULES (web-shell pass)
# ==========================================
@clamav_bp.route('/yara/rules', methods=['GET'])
@admin_required
def list_yara_rules():
    """List builtin (curated) and custom YARA rule files."""
    return jsonify(YaraScanService.list_rules()), 200


@clamav_bp.route('/yara/rules', methods=['POST'])
@admin_required
def upload_yara_rule():
    """Upload a custom .yar rule file (size-capped; requires real yara to run)."""
    data = request.get_json()
    if not data or not data.get('filename'):
        return jsonify({'error': 'filename required'}), 400
    result = YaraScanService.save_custom_rule(data['filename'], data.get('content', ''))
    if not result['success']:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@clamav_bp.route('/yara/rules/<filename>', methods=['DELETE'])
@admin_required
def delete_yara_rule(filename):
    """Delete a custom .yar rule file."""
    result = YaraScanService.delete_custom_rule(filename)
    if not result['success']:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


# ==========================================
# QUICK SCAN PRESETS
# ==========================================
@clamav_bp.route('/scan/quick', methods=['POST'])
@admin_required
def quick_scan():
    """Run a quick scan on common web directories."""
    config = SecurityService.get_config()
    scan_paths = config.get('clamav', {}).get('scan_paths', ['/var/www', '/home'])

    # Scan each path
    results = []
    for path in scan_paths:
        result = ClamAVService.scan_directory(path, recursive=True)
        results.append({'path': path, 'result': result})

    return jsonify({
        'success': True,
        'message': f'Started scans for {len(scan_paths)} directories',
        'scans': results
    }), 200


@clamav_bp.route('/scan/full', methods=['POST'])
@admin_required
def full_scan():
    """Run a full system scan."""
    result = ClamAVService.scan_directory('/', recursive=True)
    return jsonify(result), 200 if result['success'] else 400
