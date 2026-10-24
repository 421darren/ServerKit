"""Opt-in real Git checkout, Docker build/runtime and HTTP health-gate lifecycle.

SERVERKIT_REAL_PREVIEWS=1 pytest tests/test_real_generic_preview.py
Only nginx publication is replaced: this test must not alter the host's sites.
"""
import functools
import os
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
import pytest
from app import db
from app.models.application_preview import ApplicationPreview
from app.services.preview_service import PreviewService
from app.services.previews import runtime
from app.services.git_service import GitService
from app.services.build_service import BuildService
from test_previews import _mk_app

pytestmark = pytest.mark.skipif(os.environ.get('SERVERKIT_REAL_PREVIEWS') != '1',
                                reason='opt-in real Docker preview smoke')


def test_real_checkout_build_redeploy_http_and_cleanup(app, tmp_path, monkeypatch):
    def git(*args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True,
                              text=True, timeout=60).stdout.strip()
    repo = tmp_path / 'source'
    repo.mkdir()
    git('init', '-b', 'preview', cwd=repo)
    git('config', 'user.name', 'Preview Test', cwd=repo)
    git('config', 'user.email', 'preview@test.invalid', cwd=repo)
    (repo / 'Dockerfile').write_text('FROM busybox:1.36\nCOPY index.html /www/index.html\nCMD ["httpd", "-f", "-p", "8400", "-h", "/www"]\n')
    (repo / 'index.html').write_text('first-preview-commit')
    git('add', '.', cwd=repo)
    git('commit', '-m', 'first', cwd=repo)
    first = git('rev-parse', 'HEAD', cwd=repo)
    (repo / 'index.html').write_text('second-preview-commit')
    git('commit', '-am', 'second', cwd=repo)
    second = git('rev-parse', 'HEAD', cwd=repo)
    remote = tmp_path / 'remote.git'
    git('clone', '--bare', str(repo), str(remote))
    git('update-server-info', cwd=remote)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(runtime, 'ROOT', tmp_path / 'previews')
    monkeypatch.setattr(BuildService, 'BUILD_LOG_DIR', str(tmp_path / 'logs'))
    monkeypatch.setattr(BuildService, 'get_app_build_config', lambda _: {'build_method': 'dockerfile'})
    monkeypatch.setattr(GitService, 'get_app_config', lambda _: {'repo_url': f'http://127.0.0.1:{server.server_port}/remote.git'})
    monkeypatch.setattr(runtime.NginxService, 'list_sites', lambda: [])
    routes = {}
    def publish(name, kind, domains, **kwargs):
        rendered = runtime.NginxService.render_site_config(name, kind, domains, **kwargs)
        assert rendered['success']
        routes[name] = rendered['config']
        return {'success': True}
    monkeypatch.setattr(runtime.NginxService, 'create_site', publish)
    monkeypatch.setattr(runtime.NginxService, 'disable_site', lambda _: {'success': True})
    # delete returns a dict, independent of the removed config text.
    def delete(name):
        routes.pop(name, None)
        return {'success': True}
    monkeypatch.setattr(runtime.NginxService, 'delete_site', delete)
    monkeypatch.setattr(runtime.SiteDomainService, 'covering_base', lambda _: None)
    try:
        with app.app_context():
            parent = _mk_app(name='real-preview')
            PreviewService.enable_previews(parent.id, {'enabled': True, 'domain_template': 'pr-{pr_number}.example.test'})
            preview_id = None
            try:
                for sha, expected in [(first, 'first-preview-commit'), (second, 'second-preview-commit')]:
                    result = PreviewService.create_preview(parent, {'pr_number': 17, 'branch': 'preview', 'commit_sha': sha})
                    preview_id = result.get('id')
                    assert result['status'] == 'running', result
                    row = db.session.get(ApplicationPreview, preview_id)
                    state = row.get_runtime_state()
                    with urlopen(f"http://127.0.0.1:{state['port']}", timeout=10) as response:
                        assert response.read().decode() == expected
                    assert str(state['port']) in next(iter(routes.values()))
                assert PreviewService.destroy_preview(preview_id)['status'] == 'destroyed'
                assert not routes and not list(runtime.ROOT.iterdir())
                assert runtime.inspect('container', runtime.identity(preview_id, state['token'])) is None
                assert runtime.inspect('image', runtime.identity(preview_id, state['token']) + ':preview') is None
            finally:
                if preview_id:
                    PreviewService.destroy_preview(preview_id)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
