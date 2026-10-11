"""`serverkit <verb>` must not boot a second set of background daemons.

The CLI runs as `python cli.py ...`, so the app factory's `flask`-argv sniff
never matched it: every command started a job consumer, scheduler and relay
beside the live panel. Importing cli.py now opts the process out.
"""
import os
import subprocess
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE = ("import os, cli; "
         "print(os.environ.get('SERVERKIT_SKIP_BACKGROUND'))")


def _probe(**env):
    child_env = {k: v for k, v in os.environ.items()
                 if k != 'SERVERKIT_SKIP_BACKGROUND'}
    child_env.update(env)
    out = subprocess.run([sys.executable, '-c', PROBE], cwd=BACKEND,
                         env=child_env, capture_output=True, text=True,
                         timeout=120)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip().splitlines()[-1]


def test_cli_import_skips_background_daemons():
    assert _probe() == '1'


def test_explicit_operator_setting_wins():
    assert _probe(SERVERKIT_SKIP_BACKGROUND='0') == '0'
