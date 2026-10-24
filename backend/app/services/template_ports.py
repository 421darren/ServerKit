"""Host-port allocation for template installs: scans app rows, containers and live sockets, and holds a claim until the install records its port.

Mixed into TemplateService; callers keep using TemplateService."""
import re
import threading
import time
from app.exceptions import ConflictError
from app.utils.system import run_checked

# Ports handed to an install that has not written its app row (or started its
# container) yet. Without this, two installs resolving a port variable at the
# same time both saw the same port free. Single-process panel, so in-memory.
_PORT_CLAIM_TTL = 15 * 60
_claimed_ports = {}
_claimed_ports_lock = threading.Lock()


class TemplatePortsMixin:
    @classmethod
    def _managed_app_base_port(cls) -> int:
        """Return the admin-configured base port for managed apps, or 0 if unset.

        Reads the ``managed_app_base_port`` system setting. Returns 0 (meaning
        "use each template's own default") on any error, e.g. if the settings
        table isn't ready yet during early startup.
        """
        try:
            from app.services.settings_service import SettingsService
            return int(SettingsService.get('managed_app_base_port', 0) or 0)
        except Exception:
            return 0

    @classmethod
    def _find_available_port(cls, start_port: int = 8000, max_attempts: int = 1000) -> int:
        """Find an available port that's not in use by the system, Docker, or database.

        Checks:
        1. Ports assigned to existing applications in the database
        2. Docker container port mappings
        3. Socket binding test
        """
        import socket

        # Get ports from database (assigned to apps)
        db_ports = cls._get_database_used_ports()

        # Get ports currently used by Docker containers
        docker_ports = cls._get_docker_used_ports()

        # Combine all used ports
        used_ports = db_ports | docker_ports | cls._live_claims()

        for port in range(start_port, start_port + max_attempts):
            # Skip reserved/common ports
            if port < 1024:
                continue

            # Skip if already assigned in DB or Docker
            if port in used_ports:
                continue

            # Check if port is available on localhost (where Docker binds)
            try:
                # Try to bind - most reliable check
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_sock.bind(('127.0.0.1', port))
                test_sock.close()
                return port
            except OSError:
                continue
            except Exception:
                continue

        # A random port here could collide with anything; say so instead.
        raise ConflictError(
            f'No free port between {start_port} and {start_port + max_attempts - 1}')

    @staticmethod
    def _live_claims() -> set:
        now = time.monotonic()
        with _claimed_ports_lock:
            for port, at in list(_claimed_ports.items()):
                if now - at > _PORT_CLAIM_TTL:
                    del _claimed_ports[port]
            return set(_claimed_ports)

    @classmethod
    def _claim_port(cls, start_port: int = 8000) -> int:
        """Find a free port and hold it for the install about to use it."""
        while True:
            port = cls._find_available_port(start_port)
            with _claimed_ports_lock:
                if port not in _claimed_ports:
                    _claimed_ports[port] = time.monotonic()
                    return port
            start_port = port + 1

    @classmethod
    def _port_is_free(cls, port) -> bool:
        """True when nothing -- app row, container, or live socket -- holds
        ``port``. Same three sources as :meth:`_find_available_port`, asked
        about one specific port instead of scanning."""
        import socket
        try:
            port = int(port)
        except (TypeError, ValueError):
            return False
        if not 1 <= port <= 65535:
            return False
        if port in (cls._get_database_used_ports() | cls._get_docker_used_ports()
                    | cls._live_claims()):
            return False
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_sock.bind(('127.0.0.1', port))
            test_sock.close()
            return True
        except OSError:
            return False
        except Exception:
            return False

    @classmethod
    def _get_database_used_ports(cls) -> set:
        """Get all ports assigned to applications in the database."""
        used_ports = set()
        try:
            from app.models import Application
            # Deliberately unfiltered: a soft-deleted app must KEEP reserving its
            # port, or a new app takes it and restoring from the recycle bin collides.
            apps = Application.query.filter(Application.port.isnot(None)).all()
            for app in apps:
                if app.port:
                    used_ports.add(app.port)
            # A slot app holds two ports: the live one is app.port,
            # the standby's stays reserved for the switch back.
            from app.models.app_slot import AppSlot
            used_ports.update(row.host_port for row in
                              AppSlot.query.filter(AppSlot.host_port.isnot(None)).all())
        except Exception:
            pass
        return used_ports

    @classmethod
    def _get_docker_used_ports(cls) -> set:
        """Get all ports currently mapped by Docker containers."""
        used_ports = set()
        try:
            result = run_checked(['docker', 'ps', '--format', '{{.Ports}}'], timeout=10)
            if result['success']:
                # Parse port mappings like "0.0.0.0:8080->80/tcp, 127.0.0.1:3306->3306/tcp"
                import re
                for line in result['output'].strip().split('\n'):
                    if line:
                        # Find all host ports in the format "host:port->container"
                        matches = re.findall(r'(?:[\d.]+:)?(\d+)->', line)
                        for port_str in matches:
                            try:
                                used_ports.add(int(port_str))
                            except ValueError:
                                pass
        except Exception:
            pass
        return used_ports
