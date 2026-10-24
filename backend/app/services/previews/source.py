"""Prepare an independent, pinned checkout and reuse the standard builders."""
import shutil
from app.services.git_service import GitService
from app.services.build_service import BuildService
from app.utils.git_security import git_argv, git_env
from app.utils.system import run_checked
from .plan import PreviewError, relative_file


def prepare(app, preview, target, repo_url):
    result = GitService.clone_repository(str(target), repo_url, branch=preview.branch)
    if not result.get('success'):
        # Raw Git output can contain authenticated repository URLs.
        raise PreviewError('Preview repository clone failed. Check repository access and branch.')
    sha = preview.commit_sha.lower()
    # A PR must name a commit reachable from the selected same-repository branch.
    result = run_checked(git_argv('-C', str(target), 'merge-base', '--is-ancestor',
                                 sha, 'HEAD'), timeout=30, env=git_env())
    if not result.get('success'):
        raise PreviewError('Preview commit is not reachable from the selected repository branch.')
    result = run_checked(git_argv('-C', str(target), 'checkout', '--detach', sha),
                         timeout=60, env=git_env())
    if not result.get('success'):
        raise PreviewError('Could not check out the requested preview commit.')
    # Do not send clone credentials / Git metadata into a Docker build context.
    shutil.rmtree(target / '.git')


def build(app, preview, target, image):
    config = dict(BuildService.get_app_build_config(app.id) or {})
    config['app_path'] = str(target)
    method = config.get('build_method', 'auto')
    if method == 'auto':
        method = BuildService.detect_build_method(str(target))['build_method']
    if method not in ('dockerfile', 'nixpacks'):
        raise PreviewError('Previews require a Dockerfile or container buildpack; host-command builds are disabled.')
    config['build_method'] = method
    relative_file(target, config.get('dockerfile_path') or 'Dockerfile')
    relative_file(target, 'Dockerfile.serverkit')
    # Detect the PR's source, not the parent branch's persisted plan. Parent
    # build secrets are not implicitly handed to PR code.
    config.pop('buildpack_plan', None)
    config['build_args'] = {}
    config['env_vars'] = {}
    result = BuildService.build_from_config(
        f'preview-{preview.id}', config, image_tag=image,
    )
    if not result.get('success'):
        raise PreviewError('Preview image build failed. See the preview build logs.')
