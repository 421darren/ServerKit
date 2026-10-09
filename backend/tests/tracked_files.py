"""Scope tree-measuring instruments to the files that ship with the repo.

The censuses and structural guards measure ``backend/app`` by walking the
filesystem — but a dev box's ``app/plugins/`` also holds *installed* extension
copies that are not tracked in git (only the builtin extensions are). A walk
that counts those measures the machine, not the product: the raw-subprocess
ceiling picked up 4 call sites from locally-installed extensions that CI's
clean checkout can never see, which is exactly the silent-slack failure mode
the ceilings exist to prevent.

``tracked_py_files()`` returns the set of git-tracked ``.py`` paths under a
root, so an instrument can skip everything else. When git is unavailable it
returns ``None`` and callers fall back to walking everything — measuring too
much is recoverable; measuring nothing is not.

Carried extensions: this fork tracks the live copies of several extensions
under ``app/plugins/`` (upstream installs them from the registry and does not
track them). They are extension code, not core: the ceilings and inventories
are upstream's quality gates for core, so counting the carried copies would
push every ceiling over its limit without saying anything about core. They are
listed here and skipped, which makes a census of this tree see what upstream's
CI sees. Their own tests load the plugin files directly and are unaffected.
"""

import os
import subprocess

CARRIED_EXTENSIONS = (
    'serverkit-auto-updates',
    'serverkit-clamav',
    'serverkit-cloud-provision',
    'serverkit-cloudflare-ops',
    'serverkit-email',
    'serverkit-fail2ban',
    'serverkit-ftp',
    'serverkit-remote-access',
    'serverkit-wordpress',
)
_CARRIED_PREFIXES = tuple(f'app/plugins/{d}/' for d in CARRIED_EXTENSIONS)


def tracked_py_files(root):
    """Absolute, ``os.path.normcase``-normalised paths of git-tracked ``.py``
    files under *root*, or ``None`` when git cannot answer."""
    try:
        proc = subprocess.run(
            ['git', 'ls-files', '-z', '--', '.'],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return {
        os.path.normcase(os.path.abspath(os.path.join(root, rel)))
        for rel in proc.stdout.split('\0')
        if rel.endswith('.py')
        and not rel.replace(os.sep, '/').startswith(_CARRIED_PREFIXES)
    }


def is_tracked(path, tracked):
    """True when *path* is in *tracked*, or when there is no filter."""
    if tracked is None:
        return True
    return os.path.normcase(os.path.abspath(path)) in tracked
