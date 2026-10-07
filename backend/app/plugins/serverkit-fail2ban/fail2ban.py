"""Fail2ban management API — service status, jail overview, ban/unban, and
one-click install, moved out of the host's security suite (plan 47 Ph3c /
plan 55 Phase 3).

The write-half seam stays core: the panel's ``Fail2banJailService`` owns the
managed per-site jails AND the status/probe + unban primitives, so managed
brute-force protection keeps working with this extension absent. This module
delegates those three calls to core and carries only the management-surface
code (install, manual ban, cross-jail ban listing). Host-level fail2ban
surfaces stay admin-only (plan 29 #9 bucket).
"""
import subprocess
from typing import Dict

from flask import Blueprint, request, jsonify
from app.middleware.rbac import admin_required
from app.services.fail2ban_jail_service import Fail2banJailService
from app.utils.system import PackageManager, ServiceControl, run_checked

fail2ban_bp = Blueprint('security_fail2ban', __name__)


class Fail2banOps:
    """Management operations moved verbatim from the host SecurityService.

    Status/probe + unban live on the core ``Fail2banJailService``; only the
    install / manual-ban / list-all-bans surface migrated here.
    """

    @classmethod
    def install_fail2ban(cls) -> Dict:
        """Install Fail2ban."""
        try:
            manager = PackageManager.detect()
            if manager is None:
                return {'success': False, 'error': 'Unsupported package manager'}

            result = PackageManager.install('fail2ban', timeout=300)

            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}

            ServiceControl.enable('fail2ban', timeout=10)
            ServiceControl.start('fail2ban', timeout=10)

            return {'success': True, 'message': 'Fail2ban installed successfully'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Installation timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def get_all_fail2ban_bans(cls) -> Dict:
        """Get all banned IPs across all jails."""
        status = Fail2banJailService.get_fail2ban_status()
        if not status['service_running']:
            return {'success': False, 'error': 'Fail2ban is not running'}

        all_bans = []
        for jail in status['jails']:
            jail_status = Fail2banJailService.get_fail2ban_jail_status(jail)
            if jail_status.get('success'):
                for ip in jail_status.get('banned_ips', []):
                    all_bans.append({'ip': ip, 'jail': jail})

        return {'success': True, 'banned_ips': all_bans, 'total': len(all_bans)}

    @classmethod
    def ban_ip(cls, ip: str, jail: str = 'sshd') -> Dict:
        """Manually ban an IP in Fail2ban."""
        try:
            result = run_checked(['fail2ban-client', 'set', jail, 'banip', ip], timeout=10)

            if result['success']:
                return {'success': True, 'message': f'IP {ip} banned in {jail}'}
            return {'success': False, 'error': result['error'] or 'Failed to ban IP'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


@fail2ban_bp.route('/fail2ban/status', methods=['GET'])
@admin_required
def get_fail2ban_status():
    """Get Fail2ban status."""
    status = Fail2banJailService.get_fail2ban_status()
    return jsonify(status), 200


@fail2ban_bp.route('/fail2ban/install', methods=['POST'])
@admin_required
def install_fail2ban():
    """Install Fail2ban."""
    result = Fail2banOps.install_fail2ban()
    return jsonify(result), 200 if result['success'] else 400


@fail2ban_bp.route('/fail2ban/jails/<jail>', methods=['GET'])
@admin_required
def get_jail_status(jail):
    """Get status of a specific jail."""
    result = Fail2banJailService.get_fail2ban_jail_status(jail)
    return jsonify(result), 200 if result['success'] else 400


@fail2ban_bp.route('/fail2ban/bans', methods=['GET'])
@admin_required
def get_all_bans():
    """Get all banned IPs across all jails."""
    result = Fail2banOps.get_all_fail2ban_bans()
    return jsonify(result), 200 if result['success'] else 400


@fail2ban_bp.route('/fail2ban/unban', methods=['POST'])
@admin_required
def unban_ip():
    """Unban an IP address."""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({'error': 'IP address required'}), 400

    jail = data.get('jail')
    result = Fail2banJailService.unban_ip(data['ip'], jail)
    return jsonify(result), 200 if result['success'] else 400


@fail2ban_bp.route('/fail2ban/ban', methods=['POST'])
@admin_required
def ban_ip():
    """Manually ban an IP address."""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({'error': 'IP address required'}), 400

    jail = data.get('jail', 'sshd')
    result = Fail2banOps.ban_ip(data['ip'], jail)
    return jsonify(result), 200 if result['success'] else 400
