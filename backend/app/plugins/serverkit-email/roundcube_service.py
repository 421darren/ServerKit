"""Roundcube webmail management service (Docker-based)."""
import subprocess
from typing import Dict

from app.utils.system import run_checked, run_privileged, is_command_available


class RoundcubeService:
    """Service for managing Roundcube webmail via Docker."""

    CONTAINER_NAME = 'serverkit-roundcube'
    VOLUME_NAME = 'roundcube_data'
    IMAGE = 'roundcube/roundcubemail:latest'
    HOST_PORT = 9000

    @classmethod
    def get_status(cls) -> Dict:
        """Get Roundcube container status."""
        if not is_command_available('docker'):
            return {'installed': False, 'running': False, 'error': 'Docker not available'}

        try:
            result = run_checked(
                ['docker', 'inspect', '--format', '{{.State.Status}}', cls.CONTAINER_NAME],
                timeout=None)
            if not result['success']:
                return {'installed': False, 'running': False}

            status = result['output'].strip()
            return {
                'installed': True,
                'running': status == 'running',
                'status': status,
                'port': cls.HOST_PORT,
            }
        except Exception as e:
            return {'installed': False, 'running': False, 'error': str(e)}

    CONFIG_DIR = '/opt/roundcube-config'
    PLUGINS = 'markasjunk,serverkit_sso'
    PLUGIN_ROOT = '/opt/roundcube-plugins'
    SSO_CONF = '/opt/roundcube-config/sk_sso.inc.php'
    SSO_MASTER_FILE = '/etc/dovecot/master-users'
    SSO_MASTER_USER = 'sso'
    SSO_TTL = 30

    @staticmethod
    def _mail_hostname():
        """The mail server's own FQDN (Postfix myhostname), or None."""
        try:
            out = subprocess.run(['postconf', '-h', 'myhostname'], capture_output=True,
                                 text=True, timeout=10).stdout.strip()
            return out if out and '.' in out else None
        except Exception:
            return None

    @classmethod
    def _ensure_config_dir(cls):
        """Extra Roundcube config (special folders, Junk button) kept outside the container."""
        import os
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        path = os.path.join(cls.CONFIG_DIR, 'folders.inc.php')
        if not os.path.exists(path):
            with open(path, 'w') as fh:
                fh.write("<?php\n"
                         "$config['drafts_mbox'] = 'Drafts';\n"
                         "$config['sent_mbox'] = 'Sent';\n"
                         "$config['trash_mbox'] = 'Trash';\n"
                         "$config['junk_mbox'] = 'Junk';\n"
                         "$config['create_default_folders'] = true;\n"
                         "$config['protect_default_folders'] = true;\n"
                         "$config['markasjunk_spam_mbox'] = 'Junk';\n"
                         "$config['markasjunk_ham_mbox'] = 'INBOX';\n"
                         "$config['markasjunk_move_spam'] = true;\n"
                         "$config['markasjunk_move_ham'] = true;\n")
            os.chmod(path, 0o644)

    # ── One-click webmail login (no password prompt) ─────────────────────────
    @classmethod
    def ensure_sso(cls):
        """Set up the pieces for opening a mailbox in webmail without a password:
        the Roundcube login plugin, a shared signing secret, and a Dovecot master
        user that only accepts connections from this server / Docker. Idempotent."""
        import os, re, secrets, shutil, subprocess
        here = os.path.dirname(os.path.abspath(__file__))

        # 1. plugin files (copied next to the container mount)
        dest = os.path.join(cls.PLUGIN_ROOT, 'serverkit_sso')
        os.makedirs(dest, exist_ok=True)
        shutil.copyfile(os.path.join(here, 'roundcube_sso', 'serverkit_sso.php'),
                        os.path.join(dest, 'serverkit_sso.php'))
        os.chmod(cls.PLUGIN_ROOT, 0o755)
        os.chmod(dest, 0o755)
        os.chmod(os.path.join(dest, 'serverkit_sso.php'), 0o644)

        # 2. secrets live in a Roundcube config file only the web user can read
        secret = master = None
        if os.path.exists(cls.SSO_CONF):
            txt = open(cls.SSO_CONF).read()
            m1 = re.search(r"'sk_sso_secret'\]\s*=\s*'([^']+)'", txt)
            m2 = re.search(r"'sk_sso_master_pass'\]\s*=\s*'([^']+)'", txt)
            if m1 and m2:
                secret, master = m1.group(1), m2.group(1)
        fresh = not secret
        if fresh:
            secret = secrets.token_urlsafe(48)
            master = secrets.token_urlsafe(32)
            tmp = cls.SSO_CONF + '.new'
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o400)
            with os.fdopen(fd, 'w') as fh:
                fh.write("<?php\n"
                         f"$config['sk_sso_secret'] = '{secret}';\n"
                         f"$config['sk_sso_master_user'] = '{cls.SSO_MASTER_USER}';\n"
                         f"$config['sk_sso_master_pass'] = '{master}';\n")
            os.chown(tmp, 33, 33)  # www-data inside the Roundcube container
            os.replace(tmp, cls.SSO_CONF)

        # 3. Dovecot master user (hash only; the clear password never touches argv)
        if fresh or not os.path.exists(cls.SSO_MASTER_FILE):
            h = subprocess.run(['openssl', 'passwd', '-6', '-stdin'], input=master,
                               capture_output=True, text=True, timeout=15).stdout.strip()
            if not h.startswith('$6$'):
                raise RuntimeError('could not hash the master password')
            with open(cls.SSO_MASTER_FILE, 'w') as fh:
                fh.write(f"{cls.SSO_MASTER_USER}:{{SHA512-CRYPT}}{h}::::::"
                         "allow_nets=127.0.0.1,172.16.0.0/12\n")
            try:
                import grp
                os.chown(cls.SSO_MASTER_FILE, 0, grp.getgrnam('dovecot').gr_gid)
            except Exception:
                pass
            os.chmod(cls.SSO_MASTER_FILE, 0o640)

        conf = '/etc/dovecot/conf.d/10-auth.conf'
        txt = open(conf).read()
        if 'auth-master.conf.ext' not in ''.join(
                l for l in txt.splitlines(True) if not l.lstrip().startswith('#')):
            if not os.path.exists(conf + '.before-sso'):
                shutil.copyfile(conf, conf + '.before-sso')
            anchor = '!include auth-passwdfile.conf.ext'
            add = 'auth_master_user_separator = *\n!include auth-master.conf.ext\n'
            if anchor in txt:
                txt = txt.replace(anchor, add + anchor, 1)
            else:
                txt += '\n' + add
            open(conf, 'w').write(txt)
            subprocess.run(['doveadm', 'reload'], capture_output=True, timeout=30)
        return {'success': True, 'fresh': fresh}

    @classmethod
    def public_url(cls):
        """Public https/http address of webmail (webmail.<mail domain>), or None."""
        mailhost = cls._mail_hostname()
        if not mailhost or mailhost.count('.') < 2:
            return None
        domain = 'webmail.' + mailhost.split('.', 1)[1]
        existing = cls._nginx_vhost_for(domain)
        if existing is None:
            return None
        scheme = 'https' if ('443' in existing and 'ssl' in existing) else 'http'
        return f'{scheme}://{domain}'

    @classmethod
    def sso_login_url(cls, email, base_url):
        """Signed, single-use link (valid ~30 s) that logs `email` into webmail."""
        import base64, hashlib, hmac, json, os, re, secrets, time
        if not os.path.exists(cls.SSO_CONF):
            raise RuntimeError('One-click login is not set up yet (reinstall webmail)')
        txt = open(cls.SSO_CONF).read()
        m = re.search(r"'sk_sso_secret'\]\s*=\s*'([^']+)'", txt)
        if not m:
            raise RuntimeError('One-click login secret missing')
        payload = json.dumps({'e': email, 'x': int(time.time()) + cls.SSO_TTL,
                              'n': secrets.token_hex(8)}, separators=(',', ':'))
        body = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
        sig = hmac.new(m.group(1).encode(), f'v1.{body}'.encode(), hashlib.sha256).hexdigest()
        return f"{base_url.rstrip('/')}/?_task=login&_sk_sso=v1.{body}.{sig}"

    @staticmethod
    def _nginx_vhost_for(domain):
        """Return the text of an existing nginx config that already serves `domain`, else None."""
        import glob
        for pattern in ('/etc/nginx/sites-enabled/*', '/etc/nginx/conf.d/*.conf'):
            for fpath in glob.glob(pattern):
                try:
                    txt = open(fpath).read()
                except Exception:
                    continue
                for line in txt.splitlines():
                    parts = line.strip().rstrip(';').split()
                    if parts[:1] == ['server_name'] and domain in parts[1:]:
                        return txt
        return None

    @classmethod
    def install(cls, imap_host: str = None, smtp_host: str = None,
                domain: str = None) -> Dict:
        """Install Roundcube via Docker.

        imap_host/smtp_host default to the mail server's own hostname (it must match
        the mail certificate). The web port is bound to 127.0.0.1 only; public access
        goes through nginx.
        """
        if not is_command_available('docker'):
            return {'success': False, 'error': 'Docker is not installed'}

        try:
            mailhost = cls._mail_hostname()
            if not imap_host or imap_host == 'host.docker.internal':
                imap_host = mailhost or 'host.docker.internal'
            if not smtp_host or smtp_host == 'host.docker.internal':
                smtp_host = mailhost or 'host.docker.internal'

            cls._ensure_config_dir()
            cls.ensure_sso()

            # Remove existing container if any (data lives in the volume)
            run_checked(['docker', 'rm', '-f', cls.CONTAINER_NAME], timeout=None)
            run_checked(['docker', 'volume', 'create', cls.VOLUME_NAME], timeout=None)

            cmd = ['docker', 'run', '-d',
                   '--name', cls.CONTAINER_NAME,
                   '--restart', 'unless-stopped',
                   '--add-host', 'host.docker.internal:host-gateway']
            for h in sorted({imap_host, smtp_host} - {'host.docker.internal'}):
                cmd += ['--add-host', f'{h}:host-gateway']
            cmd += ['-p', f'127.0.0.1:{cls.HOST_PORT}:80',
                    '-e', f'ROUNDCUBEMAIL_DEFAULT_HOST=ssl://{imap_host}',
                    '-e', f'ROUNDCUBEMAIL_SMTP_SERVER=tls://{smtp_host}',
                    '-e', 'ROUNDCUBEMAIL_DEFAULT_PORT=993',
                    '-e', 'ROUNDCUBEMAIL_SMTP_PORT=587',
                    '-e', 'ROUNDCUBEMAIL_UPLOAD_MAX_FILESIZE=25M',
                    '-e', 'ROUNDCUBEMAIL_SKIN=elastic',
                    '-e', f'ROUNDCUBEMAIL_PLUGINS={cls.PLUGINS}',
                    '-v', f'{cls.VOLUME_NAME}:/var/roundcube/db',
                    '-v', f'{cls.CONFIG_DIR}:/var/roundcube/config:ro',
                    '-v', f'{cls.PLUGIN_ROOT}/serverkit_sso:/var/www/html/plugins/serverkit_sso:ro',
                    cls.IMAGE]
            result = run_checked(cmd, timeout=None)

            if not result['success']:
                return {'success': False,
                        'error': result['error'] or 'Failed to start container'}

            # Public URL: a supplied domain, else webmail.<mail domain> (mail.example.com
            # -> webmail.example.com), else webmail.<panel host>, else localhost:port.
            from app.services.site_domain_service import SiteDomainService
            public_url = None
            warning = None
            web_domain = domain
            if not web_domain and mailhost and mailhost.count('.') >= 2:
                web_domain = 'webmail.' + mailhost.split('.', 1)[1]
            if not web_domain:
                panel_origin = SiteDomainService.panel_origin()
                if panel_origin:
                    from urllib.parse import urlparse
                    panel_host = urlparse(panel_origin).hostname
                    if panel_host:
                        web_domain = f'webmail.{panel_host}'

            if web_domain:
                existing = cls._nginx_vhost_for(web_domain)
                if existing is not None:
                    # Already published (maybe with SSL set up by hand): leave it alone.
                    scheme = 'https' if ('443' in existing and 'ssl' in existing) else 'http'
                    public_url = f'{scheme}://{web_domain}'
                else:
                    public_url = f'http://{web_domain}'
                    proxy_res = cls.configure_nginx_proxy(web_domain)
                    if not proxy_res.get('success'):
                        warning = proxy_res.get('error')

            if not public_url:
                public_url = f'http://localhost:{cls.HOST_PORT}'

            out = {
                'success': True,
                'message': 'Roundcube installed successfully',
                'port': cls.HOST_PORT,
                'url': public_url,
                'imap_host': imap_host,
            }
            if warning:
                out['warning'] = warning
            return out
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def uninstall(cls) -> Dict:
        """Stop and remove Roundcube container."""
        try:
            run_checked(['docker', 'rm', '-f', cls.CONTAINER_NAME], timeout=None)
            return {'success': True, 'message': 'Roundcube uninstalled'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def start(cls) -> Dict:
        """Start Roundcube container."""
        try:
            result = run_checked(['docker', 'start', cls.CONTAINER_NAME], timeout=None)
            if result['success']:
                return {'success': True, 'message': 'Roundcube started'}
            return {'success': False, 'error': result['error'] or 'Start failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def stop(cls) -> Dict:
        """Stop Roundcube container."""
        try:
            result = run_checked(['docker', 'stop', cls.CONTAINER_NAME], timeout=None)
            if result['success']:
                return {'success': True, 'message': 'Roundcube stopped'}
            return {'success': False, 'error': result['error'] or 'Stop failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def restart(cls) -> Dict:
        """Restart Roundcube container."""
        try:
            result = run_checked(['docker', 'restart', cls.CONTAINER_NAME], timeout=None)
            if result['success']:
                return {'success': True, 'message': 'Roundcube restarted'}
            return {'success': False, 'error': result['error'] or 'Restart failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @classmethod
    def configure_nginx_proxy(cls, domain: str) -> Dict:
        """Create Nginx reverse proxy config for Roundcube."""
        try:
            from app.services.nginx_service import NginxService

            config = f"""# Roundcube Webmail - Managed by ServerKit
server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{cls.HOST_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 25m;
    }}
}}
"""
            site_name = f'roundcube-{domain.replace(".", "-")}'
            config_path = f'/etc/nginx/sites-available/{site_name}'
            enabled_path = f'/etc/nginx/sites-enabled/{site_name}'

            run_privileged(['tee', config_path], input=config)
            run_privileged(['ln', '-sf', config_path, enabled_path])

            # Test and reload
            test = run_privileged(['nginx', '-t'])
            if test.returncode != 0:
                # Rollback
                run_privileged(['rm', '-f', enabled_path])
                return {'success': False, 'error': f'Nginx config test failed: {test.stderr}'}

            run_privileged(['systemctl', 'reload', 'nginx'])

            return {
                'success': True,
                'message': f'Nginx proxy configured for {domain}',
                'url': f'http://{domain}',
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
