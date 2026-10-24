"""Fail2ban management API — service status, jail overview, ban/unban, and
one-click install, moved out of the host's security suite.

The write-half seam stays core: the panel's ``Fail2banJailService`` owns the
managed per-site jails AND the status/probe + unban primitives, so managed
brute-force protection keeps working with this extension absent. This module
delegates those three calls to core and carries only the management-surface
code (install, manual ban, cross-jail ban listing). Host-level fail2ban
surfaces stay admin-only.
"""
import ipaddress
import re
import subprocess
from typing import Dict, Optional, Set

from flask import Blueprint, request, jsonify
from app.middleware.rbac import admin_required
from app.services.fail2ban_jail_service import Fail2banJailService
from app.utils.system import PackageManager, ServiceControl, run_checked

fail2ban_bp = Blueprint('security_fail2ban', __name__)

_JAIL_RE = re.compile(r'^[A-Za-z0-9_.-]{1,64}$')


def validate_ip(value) -> Optional[str]:
    """Return the normalised IP string, or None if it must not be banned.

    Rejects anything that is not a literal IP address and addresses that can
    never be a sensible ban target (loopback, unspecified, multicast).
    """
    try:
        addr = ipaddress.ip_address(str(value).strip())
    except ValueError:
        return None
    if addr.is_loopback or addr.is_unspecified or addr.is_multicast:
        return None
    return str(addr)


def valid_jail_name(value) -> bool:
    return bool(value) and bool(_JAIL_RE.match(str(value)))


def local_addresses() -> Set[str]:
    """IP addresses configured on this host (never ban the server itself)."""
    found: Set[str] = set()
    try:
        import psutil
        for addrs in psutil.net_if_addrs().values():
            for a in addrs:
                host = a.address.split('%')[0]
                try:
                    found.add(str(ipaddress.ip_address(host)))
                except ValueError:
                    pass
    except Exception:
        pass
    return found


def requester_ip() -> Optional[str]:
    """The admin's own address, so they cannot ban themselves."""
    fwd = request.headers.get('X-Forwarded-For', '')
    candidate = fwd.split(',')[0].strip() if fwd else (request.remote_addr or '')
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None



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
    def ban_ip(cls, ip: str, jail: str = 'sshd', protected: Optional[Set[str]] = None) -> Dict:
        """Manually ban an IP in Fail2ban.

        Refuses malformed input and addresses that would lock the admin or
        the server itself out.
        """
        clean = validate_ip(ip)
        if clean is None:
            return {'success': False, 'error': 'Invalid or non-bannable IP address'}
        if not valid_jail_name(jail):
            return {'success': False, 'error': 'Invalid jail name'}
        if clean in (protected or set()) or clean in local_addresses():
            return {'success': False,
                    'error': 'Refusing to ban this address: it is the server itself or your own connection'}
        try:
            result = run_checked(['fail2ban-client', 'set', jail, 'banip', clean], timeout=10)

            if result['success']:
                return {'success': True, 'message': f'IP {clean} banned in {jail}'}
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
    clean = validate_ip(data['ip'])
    if clean is None:
        return jsonify({'success': False, 'error': 'Invalid IP address'}), 400
    if jail is not None and not valid_jail_name(jail):
        return jsonify({'success': False, 'error': 'Invalid jail name'}), 400
    result = Fail2banJailService.unban_ip(clean, jail)
    return jsonify(result), 200 if result['success'] else 400


@fail2ban_bp.route('/fail2ban/ban', methods=['POST'])
@admin_required
def ban_ip():
    """Manually ban an IP address."""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({'error': 'IP address required'}), 400

    jail = data.get('jail', 'sshd')
    me = requester_ip()
    result = Fail2banOps.ban_ip(data['ip'], jail, protected={me} if me else set())
    return jsonify(result), 200 if result['success'] else 400
