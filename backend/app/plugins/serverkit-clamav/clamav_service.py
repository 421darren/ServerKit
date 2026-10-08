"""ClamAV malware-scanning service — moved verbatim out of the host's
``SecurityService`` (plan 47 Ph3d / plan 55 Phase 3).

Carries the ClamAV install/status/definitions surface, single-file and
directory scans (background thread + status polling), and the quarantine
mechanics (list / move / delete / restore with the ``.meta.json`` restore
sidecar). The config store and the scan/alert logs + notification fan-out
stay on the core ``SecurityService`` — this class calls those helpers rather
than duplicating the files they own, so a panel without this extension keeps
one security.json / security_scans.log / security_alerts.log.
"""

import os
import json
import shutil
import subprocess
import threading
from datetime import datetime
from typing import Dict, Optional

from app import paths
from app.services.security_service import SecurityService
from app.utils.system import (
    PackageManager,
    ServiceControl,
    run_checked,
)


def _inside(base: str, target: str) -> bool:
    """True if target resolves to a path strictly inside base (no sibling-prefix tricks)."""
    base = os.path.realpath(base)
    target = os.path.realpath(target)
    try:
        return os.path.commonpath([base, target]) == base and target != base
    except ValueError:
        return False


class ClamAVService:
    """ClamAV scanning + quarantine, on top of core config/log/notify seams."""

    # Scan status tracking
    _current_scan = None
    _scan_thread = None

    # ==========================================
    # CLAMAV INTEGRATION
    # ==========================================
    @classmethod
    def get_clamav_status(cls) -> Dict:
        """Get ClamAV installation and service status."""
        result = {
            'installed': False,
            'service_running': False,
            'version': None,
            'database_version': None,
            'last_update': None,
            'definitions_count': None
        }

        # Check if ClamAV is installed
        try:
            version_output = run_checked(['clamscan', '--version'], timeout=10)
            if version_output['success']:
                result['installed'] = True
                result['version'] = version_output['output'].strip()
        except Exception:  # noqa: BLE001 - probe only; absence is the answer
            pass

        # Check if clamd service is running
        try:
            result['service_running'] = ServiceControl.is_active('clamav-daemon')
            if not result['service_running']:
                # Try alternative service name
                result['service_running'] = ServiceControl.is_active('clamd')
        except Exception:
            pass

        # Get database info
        try:
            db_path = '/var/lib/clamav'
            if os.path.exists(db_path):
                for db_file in ['main.cvd', 'main.cld', 'daily.cvd', 'daily.cld']:
                    full_path = os.path.join(db_path, db_file)
                    if os.path.exists(full_path):
                        stat = os.stat(full_path)
                        result['last_update'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        break
        except Exception:
            pass

        return result

    @classmethod
    def install_clamav(cls) -> Dict:
        """Install ClamAV packages."""
        try:
            manager = PackageManager.detect()
            if manager is None:
                return {'success': False, 'error': 'Unsupported package manager'}

            if manager == 'apt':
                packages = ['clamav', 'clamav-daemon', 'clamav-freshclam']
            else:
                packages = ['clamav', 'clamd', 'clamav-update']

            result = PackageManager.install(packages, timeout=300)

            if result.returncode != 0:
                return {'success': False, 'error': result.stderr}

            # Update virus definitions
            cls.update_definitions()

            return {'success': True, 'message': 'ClamAV installed successfully'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Installation timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def update_definitions(cls) -> Dict:
        """Update ClamAV virus definitions."""
        try:
            # Stop freshclam if running to avoid conflicts
            ServiceControl.stop('clamav-freshclam', timeout=10)

            result = run_checked(['freshclam'], timeout=300)

            # Restart freshclam
            ServiceControl.start('clamav-freshclam', timeout=10)

            if result['success']:
                return {'success': True, 'message': 'Definitions updated',
                        'output': result['output']}

            if result['returncode'] is None:
                # Never ran: no freshclam, or it outlived the timeout. Not the
                # same as "the update reported a problem".
                return {'success': False, 'error': result['error']}

            # Return code 1 might just mean "already up to date"
            if ('up to date' in result['output'].lower()
                    or 'up to date' in result['stderr'].lower()):
                return {'success': True, 'message': 'Definitions already up to date'}

            return {'success': False, 'error': result['stderr'] or result['output']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def start_clamav(cls) -> Dict:
        """Start and enable the ClamAV daemon.

        Debian ships the daemon as ``clamav-daemon``; RHEL and others call it
        ``clamd`` — try both, mirroring :meth:`get_clamav_status`. ``install``
        does not start the daemon, so this backs the "Start service" posture fix.
        """
        for service in ('clamav-daemon', 'clamd'):
            try:
                ServiceControl.enable(service, timeout=15)
                result = ServiceControl.start(service, timeout=30)
            except FileNotFoundError:
                return {'success': False, 'error': 'systemctl not found (not a Linux host?)'}
            except subprocess.TimeoutExpired:
                return {'success': False, 'error': 'Starting ClamAV timed out'}
            except Exception as e:
                return {'success': False, 'error': str(e)}

            if getattr(result, 'returncode', 1) == 0 and ServiceControl.is_active(service):
                return {'success': True, 'message': f'{service} started'}

        return {'success': False, 'error': 'Could not start the ClamAV service. Is ClamAV installed?'}

    @classmethod
    def scan_file(cls, file_path: str) -> Dict:
        """Scan a single file for malware."""
        if not os.path.exists(file_path):
            return {'success': False, 'error': 'File not found'}

        try:
            result = run_checked(['clamscan', '--no-summary', '--', os.path.abspath(file_path)], timeout=60)

            # clamscan exit 1 means INFECTED, not "the command failed" — read
            # the code, not result['success'].
            infected = result['returncode'] == 1
            scan_result = {
                'success': True,
                'file': file_path,
                'infected': infected,
                'output': result['output'].strip(),
                'scanned_at': datetime.now().isoformat()
            }

            if infected:
                # Log and send notification (core helpers — the logs and the
                # notification fan-out stay on the host SecurityService).
                SecurityService._log_alert('malware', f'Malware detected in {file_path}', {
                    'file': file_path,
                    'output': result['output'].strip()
                })
                SecurityService._send_security_notification(
                    'malware_detected',
                    f'Malware detected: {file_path}',
                    severity='critical'
                )

            return scan_result

        except FileNotFoundError:
            return {'success': False, 'error': 'clamscan not found. Is ClamAV installed?'}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Scan timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def scan_directory(cls, directory: str, recursive: bool = True) -> Dict:
        """Start a directory scan (runs in background for large directories)."""
        if not os.path.isdir(directory):
            return {'success': False, 'error': 'Directory not found'}

        if cls._scan_thread and cls._scan_thread.is_alive():
            return {'success': False, 'error': 'A scan is already in progress'}

        # Initialize scan status
        cls._current_scan = {
            'status': 'running',
            'directory': directory,
            'started_at': datetime.now().isoformat(),
            'files_scanned': 0,
            'infected_files': [],
            'errors': []
        }

        # Start scan in background thread
        cls._scan_thread = threading.Thread(
            target=cls._run_directory_scan,
            args=(directory, recursive),
            daemon=True
        )
        cls._scan_thread.start()

        return {
            'success': True,
            'message': f'Scan started for {directory}',
            'scan_id': cls._current_scan['started_at']
        }

    @classmethod
    def _run_directory_scan(cls, directory: str, recursive: bool) -> None:
        """Execute directory scan (internal method)."""
        config = SecurityService.get_config()
        exclude_paths = config.get('clamav', {}).get('exclude_paths', [])

        try:
            cmd = ['clamscan']
            if recursive:
                cmd.append('-r')
            cmd.append('--infected')  # summary kept: it carries the scanned-file count

            # Add exclusions
            for exclude in exclude_paths:
                cmd.extend(['--exclude', exclude])

            cmd.extend(['--', os.path.abspath(directory)])

            result = run_checked(cmd, timeout=3600)  # 1 hour

            # Parse output
            infected_files = []
            files_scanned = 0
            for line in result['output'].strip().split('\n'):
                line = line.rstrip()
                if line.endswith(' FOUND') and ': ' in line:
                    # rsplit: the signature name is last, the path may contain ': '
                    infected_files.append(line.rsplit(': ', 1)[0])
                elif line.startswith('Scanned files:'):
                    try:
                        files_scanned = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass

            # clamscan: 0 clean, 1 infected, anything else = the scan itself failed
            if result['returncode'] not in (0, 1):
                cls._current_scan['status'] = 'error'
                cls._current_scan['error'] = (result['output'] or 'clamscan failed').strip()[-500:]
                cls._current_scan['completed_at'] = datetime.now().isoformat()
                return

            cls._current_scan['files_scanned'] = files_scanned
            cls._current_scan['status'] = 'completed'
            cls._current_scan['completed_at'] = datetime.now().isoformat()
            cls._current_scan['infected_files'] = infected_files
            cls._current_scan['output'] = result['output']

            # Log scan result
            SecurityService._log_scan(cls._current_scan)

            # Send notification if malware found
            if infected_files:
                SecurityService._send_security_notification(
                    'malware_detected',
                    f'Malware detected in {len(infected_files)} file(s) during scan of {directory}',
                    severity='critical',
                    details={'files': infected_files}
                )

        except subprocess.TimeoutExpired:
            cls._current_scan['status'] = 'timeout'
            cls._current_scan['error'] = 'Scan timed out after 1 hour'
        except Exception as e:
            cls._current_scan['status'] = 'error'
            cls._current_scan['error'] = str(e)

    @classmethod
    def get_scan_status(cls) -> Dict:
        """Get current scan status."""
        if cls._current_scan is None:
            return {'status': 'idle', 'message': 'No scan in progress'}
        return cls._current_scan.copy()

    @classmethod
    def cancel_scan(cls) -> Dict:
        """Cancel running scan."""
        if cls._scan_thread and cls._scan_thread.is_alive():
            # We can't easily kill the subprocess, but we can mark it
            cls._current_scan['status'] = 'cancelled'
            return {'success': True, 'message': 'Scan marked as cancelled'}
        return {'success': False, 'error': 'No scan running'}

    @classmethod
    def quarantine_file(cls, file_path: str) -> Dict:
        """Move infected file to quarantine (with a sidecar recording the
        original location so it can be restored)."""
        config = SecurityService.get_config()
        quarantine_path = config.get('clamav', {}).get('quarantine_path', paths.SERVERKIT_QUARANTINE_DIR)

        if not os.path.exists(file_path):
            return {'success': False, 'error': 'File not found'}

        # Never quarantine something already inside the quarantine directory.
        if os.path.abspath(file_path).startswith(os.path.abspath(quarantine_path) + os.sep):
            return {'success': False, 'error': 'File is already in quarantine'}

        try:
            # Create quarantine directory
            os.makedirs(quarantine_path, exist_ok=True)

            # Generate unique quarantine name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_name = os.path.basename(file_path)
            quarantine_name = f"{timestamp}_{original_name}.quarantine"
            quarantine_full_path = os.path.join(quarantine_path, quarantine_name)

            # Move file
            shutil.move(file_path, quarantine_full_path)
            try:
                os.chmod(quarantine_full_path, 0o600)  # never leave a quarantined file executable
            except OSError:
                pass

            # Sidecar with the original location (enables restore)
            try:
                with open(quarantine_full_path + '.meta.json', 'w') as f:
                    json.dump({
                        'original_path': os.path.abspath(file_path),
                        'quarantined_at': datetime.now().isoformat(),
                    }, f)
            except Exception:
                pass  # restore becomes unavailable, quarantine itself succeeded

            # Log the quarantine action
            SecurityService._log_alert('quarantine', f'File quarantined: {file_path}', {
                'original_path': file_path,
                'quarantine_path': quarantine_full_path
            })

            return {
                'success': True,
                'message': 'File quarantined',
                'original_path': file_path,
                'quarantine_path': quarantine_full_path
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def get_quarantined_files(cls) -> Dict:
        """List quarantined files."""
        config = SecurityService.get_config()
        quarantine_path = config.get('clamav', {}).get('quarantine_path', paths.SERVERKIT_QUARANTINE_DIR)

        if not os.path.exists(quarantine_path):
            return {'success': True, 'files': []}

        try:
            files = []
            for filename in os.listdir(quarantine_path):
                if filename.endswith('.meta.json'):
                    continue  # restore sidecars, not quarantined payloads
                full_path = os.path.join(quarantine_path, filename)
                stat = os.stat(full_path)
                entry = {
                    'name': filename,
                    'path': full_path,
                    'size': stat.st_size,
                    'quarantined_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'original_path': None,
                }
                meta = cls._read_quarantine_meta(full_path)
                if meta:
                    entry['original_path'] = meta.get('original_path')
                    entry['quarantined_at'] = meta.get('quarantined_at') or entry['quarantined_at']
                files.append(entry)

            return {'success': True, 'files': files}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def delete_quarantined_file(cls, filename: str) -> Dict:
        """Permanently delete a quarantined file."""
        config = SecurityService.get_config()
        quarantine_path = config.get('clamav', {}).get('quarantine_path', paths.SERVERKIT_QUARANTINE_DIR)
        if filename != os.path.basename(filename) or filename in ('', '.', '..'):
            return {'success': False, 'error': 'Invalid file path'}
        file_path = os.path.join(quarantine_path, filename)

        # Security check: ensure file is in quarantine directory
        if not _inside(quarantine_path, file_path):
            return {'success': False, 'error': 'Invalid file path'}

        if not os.path.lexists(file_path):
            return {'success': False, 'error': 'File not found'}

        try:
            os.remove(file_path)
            try:
                os.remove(file_path + '.meta.json')
            except OSError:
                pass
            return {'success': True, 'message': 'File deleted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def _read_quarantine_meta(cls, quarantine_full_path: str) -> Optional[Dict]:
        """Read the restore sidecar for a quarantined file, if present."""
        try:
            with open(quarantine_full_path + '.meta.json', 'r') as f:
                return json.load(f)
        except Exception:
            return None

    @classmethod
    def restore_quarantined_file(cls, filename: str) -> Dict:
        """Move a quarantined file back to its recorded original location."""
        config = SecurityService.get_config()
        quarantine_path = config.get('clamav', {}).get('quarantine_path', paths.SERVERKIT_QUARANTINE_DIR)
        if filename != os.path.basename(filename) or filename in ('', '.', '..') \
                or filename.endswith('.meta.json'):
            return {'success': False, 'error': 'Invalid file path'}
        file_path = os.path.join(quarantine_path, filename)

        # Security check: ensure file is in quarantine directory
        if not _inside(quarantine_path, file_path):
            return {'success': False, 'error': 'Invalid file path'}

        if not os.path.lexists(file_path):
            return {'success': False, 'error': 'File not found'}

        meta = cls._read_quarantine_meta(file_path)
        original_path = (meta or {}).get('original_path')
        if not original_path:
            return {'success': False,
                    'error': 'Original location unknown — this file was quarantined '
                             'before restore metadata existed'}

        if os.path.exists(original_path):
            return {'success': False,
                    'error': f'A file already exists at {original_path}; '
                             'remove it first to restore'}

        try:
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(file_path, original_path)
            try:
                os.remove(file_path + '.meta.json')
            except OSError:
                pass

            SecurityService._log_alert('quarantine_restore', f'File restored from quarantine: {original_path}', {
                'quarantine_name': filename,
                'restored_to': original_path,
            })
            return {'success': True, 'message': 'File restored',
                    'restored_to': original_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
