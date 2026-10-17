"""Docker Mailserver administration for local and remote ServerKit servers.

This service provides domain-level mail operations while keeping Docker
transport details behind RemoteDockerService.  Local targets execute through
DockerService; remote targets use the ServerKit agent.
"""

from typing import Any, Dict

from app.services.remote_docker_service import RemoteDockerService


class MailServerService:
    """Manage a docker-mailserver container through ServerKit."""

    DEFAULT_CONTAINER = 'mailserver'

    @staticmethod
    def _parse_mailbox_quota(raw: str) -> Dict[str, Any]:
        """Parse doveadm quota output into structured values."""
        quota = {
            'storage': None,
            'messages': None,
            'limit': None,
            'percent': None,
        }

        for line in (raw or '').splitlines():
            parts = line.split()
            if len(parts) < 5 or parts[0] == 'Quota':
                continue

            quota_type = parts[1]

            try:
                value = int(parts[2])
            except (TypeError, ValueError):
                value = None

            limit_raw = parts[3]
            limit = None if limit_raw == '-' else limit_raw

            try:
                percent = int(parts[4])
            except (TypeError, ValueError):
                percent = None

            if quota_type == 'STORAGE':
                quota['storage'] = value
                quota['limit'] = limit
                quota['percent'] = percent
            elif quota_type == 'MESSAGE':
                quota['messages'] = value

        return quota

    @staticmethod
    def _parse_mailbox_status(raw: str) -> Dict[str, Any]:
        """Parse doveadm mailbox status output into structured values."""
        status = {
            'messages': None,
            'recent': None,
            'unseen': None,
            'uidnext': None,
            'uidvalidity': None,
            'highestmodseq': None,
            'vsize': None,
            'firstsaved': None,
            'guid': None,
        }

        line = (raw or '').strip().splitlines()[0] if (raw or '').strip() else ''

        if line.startswith('INBOX '):
            line = line[6:]

        for item in line.split():
            if '=' not in item:
                continue

            key, value = item.split('=', 1)

            if key not in status:
                continue

            if key in {'firstsaved', 'guid'}:
                status[key] = value
                continue

            try:
                status[key] = int(value)
            except ValueError:
                status[key] = value

        return status

    @staticmethod
    def list_mailboxes(
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Return the mailbox listing reported by docker-mailserver."""
        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['setup', 'email', 'list'],
            timeout_seconds=30,
            user_id=user_id,
        )

        if not result.get('success'):
            return result

        data = result.get('data') or {}
        exit_code = data.get('exit_code', 0)

        if exit_code != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to list mailboxes',
                'data': data,
            }

        return {
            'success': True,
            'mailboxes_raw': data.get('stdout', ''),
        }


    @staticmethod
    def get_mailbox_details(
        email: str,
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Return quota and INBOX status information for a mailbox."""
        email = (email or '').strip()
        if not email or '@' not in email:
            return {'success': False, 'error': 'A valid email address is required'}

        quota_result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['doveadm', 'quota', 'get', '-u', email],
            timeout_seconds=30,
            user_id=user_id,
        )

        if not quota_result.get('success'):
            return quota_result

        quota_data = quota_result.get('data') or {}
        if quota_data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': quota_data.get('stderr') or 'Failed to get mailbox quota',
                'data': quota_data,
            }

        status_result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['doveadm', 'mailbox', 'status', '-u', email, 'all', 'INBOX'],
            timeout_seconds=30,
            user_id=user_id,
        )

        if not status_result.get('success'):
            return status_result

        status_data = status_result.get('data') or {}
        if status_data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': status_data.get('stderr') or 'Failed to get mailbox status',
                'data': status_data,
            }

        quota = MailServerService._parse_mailbox_quota(
            quota_data.get('stdout', '')
        )
        inbox = MailServerService._parse_mailbox_status(
            status_data.get('stdout', '')
        )

        return {
            'success': True,
            'email': email,
            'quota': quota,
            'inbox': inbox,
        }


    @staticmethod
    def add_mailbox(
        email: str,
        password: str,
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Create a docker-mailserver mailbox without persisting its password."""
        email = (email or '').strip()
        if not email or '@' not in email:
            return {'success': False, 'error': 'A valid email address is required'}
        if not password:
            return {'success': False, 'error': 'A password is required'}

        cmd = ['setup', 'email', 'add', email, password]
        audit_cmd = ['setup', 'email', 'add', email, '[redacted]']

        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=cmd,
            audit_cmd=audit_cmd,
            timeout_seconds=30,
            user_id=user_id,
        )

        if not result.get('success'):
            return result

        data = result.get('data') or {}
        if data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to create mailbox',
                'data': data,
            }

        return {
            'success': True,
            'email': email,
            'stdout': data.get('stdout', ''),
        }

    @staticmethod
    def update_mailbox_password(
        email: str,
        password: str,
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Update a docker-mailserver mailbox password without persisting it."""
        email = (email or '').strip()
        if not email or '@' not in email:
            return {'success': False, 'error': 'A valid email address is required'}
        if not password:
            return {'success': False, 'error': 'A password is required'}

        cmd = ['setup', 'email', 'update', email, password]
        audit_cmd = ['setup', 'email', 'update', email, '[redacted]']

        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=cmd,
            audit_cmd=audit_cmd,
            timeout_seconds=30,
            user_id=user_id,
        )

        if not result.get('success'):
            return result

        data = result.get('data') or {}
        if data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to update mailbox password',
                'data': data,
            }

        return {
            'success': True,
            'email': email,
        }

    @staticmethod
    def delete_mailbox(
        email: str,
        delete_mail_data: bool = False,
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Delete a docker-mailserver mailbox, optionally including mail data."""
        email = (email or '').strip()
        if not email or '@' not in email:
            return {'success': False, 'error': 'A valid email address is required'}

        delete_option = '-y' if delete_mail_data else '-n'

        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['setup', 'email', 'del', delete_option, email],
            timeout_seconds=30,
            user_id=user_id,
        )

        if not result.get('success'):
            return result

        data = result.get('data') or {}
        if data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to delete mailbox',
                'data': data,
            }

        return {
            'success': True,
            'email': email,
            'mail_data_deleted': delete_mail_data,
        }

    @staticmethod
    def _is_missing_alias_file(result: Dict[str, Any]) -> bool:
        """docker-mailserver has no postfix-virtual.cf until the first alias.

        The 'does not exist' message comes back in different places: local
        exec puts it in stderr, the remote agent may put it in stdout, in a
        combined 'output' field, or only in the top-level error.
        """
        data = result.get('data') or {}
        text = ' '.join(str(x) for x in (
            result.get('error'), data.get('stderr'), data.get('stdout'),
            data.get('output'),
        ) if x)
        return 'postfix-virtual.cf' in text and 'does not exist' in text

    @staticmethod
    def list_aliases(
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Return the alias listing reported by docker-mailserver."""
        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['setup', 'alias', 'list'],
            timeout_seconds=30,
            user_id=user_id,
        )

        data = result.get('data') or {}
        failed = not result.get('success') or data.get('exit_code', 0) != 0
        if failed and MailServerService._is_missing_alias_file(result):
            # No alias has been created yet: that is an empty list, not an error.
            return {
                'success': True,
                'aliases_raw': '',
            }

        if not result.get('success'):
            return result

        if data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to list aliases',
                'data': data,
            }

        return {
            'success': True,
            'aliases_raw': data.get('stdout', ''),
        }

    @staticmethod
    def add_alias(
        alias: str,
        recipient: str,
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Add a docker-mailserver alias recipient."""
        alias = (alias or '').strip()
        recipient = (recipient or '').strip()

        if not alias or '@' not in alias:
            return {'success': False, 'error': 'A valid alias email address is required'}
        if not recipient or '@' not in recipient:
            return {'success': False, 'error': 'A valid recipient email address is required'}

        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['setup', 'alias', 'add', alias, recipient],
            timeout_seconds=30,
            user_id=user_id,
        )

        if not result.get('success'):
            return result

        data = result.get('data') or {}
        if data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to add alias',
                'data': data,
            }

        return {
            'success': True,
            'alias': alias,
            'recipient': recipient,
        }

    @staticmethod
    def delete_alias(
        alias: str,
        recipient: str,
        server_id: str = 'local',
        container_id: str = DEFAULT_CONTAINER,
        user_id: int = None,
    ) -> Dict[str, Any]:
        """Remove one recipient from a docker-mailserver alias."""
        alias = (alias or '').strip()
        recipient = (recipient or '').strip()

        if not alias or '@' not in alias:
            return {'success': False, 'error': 'A valid alias email address is required'}
        if not recipient or '@' not in recipient:
            return {'success': False, 'error': 'A valid recipient email address is required'}

        result = RemoteDockerService.exec_command(
            server_id=server_id,
            container_id=container_id,
            cmd=['setup', 'alias', 'del', alias, recipient],
            timeout_seconds=30,
            user_id=user_id,
        )

        if not result.get('success'):
            return result

        data = result.get('data') or {}
        if data.get('exit_code', 0) != 0:
            return {
                'success': False,
                'error': data.get('stderr') or 'Failed to delete alias recipient',
                'data': data,
            }

        return {
            'success': True,
            'alias': alias,
            'recipient': recipient,
        }

