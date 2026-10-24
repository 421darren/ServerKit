"""Host effects for one journalled preview generation; never operate on parent resources."""
import json
import shutil
from pathlib import Path
from app import db, paths
from app.services.docker_service import DockerService
from app.services.nginx_service import NginxService
from app.services.site_domain_service import SiteDomainService
from app.services import health_gate
from .plan import PreviewError, identity, workspace

ROOT = Path(paths.SERVERKIT_DIR) / 'previews'
LABEL = 'serverkit.preview'


def save(preview, state):
    preview.set_runtime_state(state)
    db.session.commit()


def inspect(kind, name):
    result = DockerService.run([kind, 'inspect', name], timeout=30)
    if result.get('success'):
        return json.loads(result['output'])[0]
    error = (result.get('error') or '').lower()
    if 'no such' in error:
        return None
    raise PreviewError('Cannot inspect preview resources; cleanup must be retried.')


def start(app, preview, state, inherit_environment=False):
    name = identity(preview.id, state['token'])
    state['container'] = True
    save(preview, state)  # intent before docker run, even if it partially fails
    env = {'SERVERKIT_PREVIEW': 'true', 'SERVERKIT_PR_NUMBER': str(preview.pr_number),
           'SERVERKIT_PREVIEW_BRANCH': preview.branch}
    if inherit_environment:
        from app.services.env_service import EnvService
        entries, complete = EnvService._effective_entries(app)
        if not complete:
            raise PreviewError('Inherited environment is incomplete; preview deployment stopped.')
        env = {**{key: value['value'] for key, value in entries.items()}, **env}
    result = DockerService.run_container(
        image=name + ':preview', name=name, ports=[f'127.0.0.1::{app.port}'],
        env=env, restart_policy='unless-stopped', labels={LABEL: str(preview.id)},
    )
    if not result.get('success'):
        raise PreviewError('Could not start the preview container.')
    info = inspect('container', name)
    if not info or info.get('Config', {}).get('Labels', {}).get(LABEL) != str(preview.id):
        raise PreviewError('Preview container ownership could not be verified.')
    bindings = info.get('NetworkSettings', {}).get('Ports', {}).get(f'{app.port}/tcp') or []
    binding = next((b for b in bindings if b.get('HostIp') == '127.0.0.1'), None)
    if not binding:
        raise PreviewError('Preview container has no loopback HTTP port.')
    state['port'] = int(binding['HostPort'])
    state['container_id'] = info['Id']
    save(preview, state)
    health_gate.gate_for_app(app, port=state['port'], container=name)
    info = inspect('container', name)
    if not info or not info.get('State', {}).get('Running'):
        raise PreviewError('Preview container stopped during its health check.')


def publish(preview, state):
    name = identity(preview.id, state['token'])
    cert = key = None
    base = SiteDomainService.covering_base(preview.domain)
    # A wildcard certificate covers exactly one label, not pr.app.base.
    if base and preview.domain.endswith('.' + base) and preview.domain.count('.') == base.count('.') + 1:
        if SiteDomainService.https_enabled(base):
            cert, key = SiteDomainService.wildcard_cert_paths(base)
    state['scheme'] = 'https' if cert and key else 'http'
    state['vhost'] = True
    save(preview, state)
    result = NginxService.create_site(name, 'docker', [preview.domain],
                                      port=state['port'], ssl_cert=cert, ssl_key=key)
    if not result.get('success'):
        raise PreviewError('Preview routing could not be published.')


def cleanup(preview):
    """Idempotent, fail closed. Retain each intent until its removal succeeds."""
    state = preview.get_runtime_state()
    if not state:
        if preview.runtime_state and preview.runtime_state != '{}':
            raise PreviewError('Preview resource ledger is invalid; refusing untracked cleanup.')
        return
    name = identity(preview.id, state.get('token', ''))
    target = workspace(ROOT, preview.id, state['token'])
    if state.get('vhost'):
        # delete_site historically ignores disable failures. Check disable first
        # so nginx cannot continue serving a resource reported as destroyed.
        if not NginxService.disable_site(name).get('success'):
            raise PreviewError('Preview routing cleanup failed; retry deletion.')
        if not NginxService.delete_site(name).get('success'):
            raise PreviewError('Preview vhost cleanup failed; retry deletion.')
        state['vhost'] = False
        save(preview, state)
    if state.get('container'):
        info = inspect('container', name)
        if info:
            if info.get('Config', {}).get('Labels', {}).get(LABEL) != str(preview.id):
                raise PreviewError('Refusing to delete a container without preview ownership.')
            if not DockerService.remove_container(name, force=True, volumes=True).get('success'):
                raise PreviewError('Preview container cleanup failed; retry deletion.')
        state['container'] = False
        preview.set_container_ids([])
        save(preview, state)
    if state.get('image'):
        if inspect('image', name + ':preview') is not None:
            if not DockerService.remove_image(name + ':preview', force=False).get('success'):
                raise PreviewError('Preview image cleanup failed; retry deletion.')
        state['image'] = False
        save(preview, state)
    if state.get('source'):
        if target.exists():
            shutil.rmtree(target)
        state['source'] = False
        save(preview, state)
    preview.set_container_ids([])
    save(preview, {})
