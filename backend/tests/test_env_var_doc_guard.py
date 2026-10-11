"""Every environment variable the backend reads is listed in docs/ENVIRONMENT.md.

About 30 of the ~70 variables were documented nowhere, so operators found
settings like the encryption-key file or the extension signing keys only by
reading the source.
"""
import ast
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
DOC = os.path.join(os.path.dirname(BACKEND), 'docs', 'ENVIRONMENT.md')

# Read from the environment but not panel settings.
NOT_SETTINGS = {
    'PATH',     # passed through to child processes
    'APPDATA',  # Windows dev fallback for the uptime history file
}

ENV_HELPER = re.compile(r'^_?env_[a-z]+$')


def _sources():
    yield os.path.join(BACKEND, 'config.py')
    yield os.path.join(BACKEND, 'run.py')
    for root, dirs, files in os.walk(os.path.join(BACKEND, 'app')):
        dirs[:] = [d for d in dirs if d not in ('plugins', '__pycache__')]
        for name in files:
            if name.endswith('.py'):
                yield os.path.join(root, name)


def _string_constants(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    out[target.id] = node.value.value
    return out


def _read_names(path):
    tree = ast.parse(open(path, encoding='utf-8').read())
    consts = _string_constants(tree)

    def literal(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return consts.get(node.id)
        return None

    for node in ast.walk(tree):
        key = None
        if isinstance(node, ast.Call) and node.args:
            func = ast.unparse(node.func)
            short = func.rsplit('.', 1)[-1]
            if func in ('os.environ.get', 'os.getenv', 'os.environ.setdefault') \
                    or ENV_HELPER.match(short) or short == 'env_bool':
                key = literal(node.args[0])
        elif isinstance(node, ast.Subscript) and ast.unparse(node.value) == 'os.environ' \
                and isinstance(node.ctx, ast.Load):
            key = literal(node.slice)
        if key and re.fullmatch(r'[A-Z][A-Z0-9_]+', key):
            yield key


def test_every_env_var_read_is_documented():
    documented = set(re.findall(r'^\| `([A-Z][A-Z0-9_]+)`', open(DOC, encoding='utf-8').read(), re.M))
    read = {}
    for path in _sources():
        for key in _read_names(path):
            read.setdefault(key, os.path.relpath(path, BACKEND))
    missing = sorted(k for k in read if k not in documented and k not in NOT_SETTINGS)
    assert not missing, (
        'Add these to docs/ENVIRONMENT.md: '
        + ', '.join(f'{k} ({read[k]})' for k in missing))


def test_the_scan_sees_reads_through_helpers_and_constants():
    """The guard is only as good as its scan: config.py reads through
    _env_bool/_env_int and safe_http names its variable in a constant."""
    names = set()
    for path in _sources():
        names.update(_read_names(path))
    assert {'TRUST_PROXY_HEADERS', 'AUTH_IP_MAX_ATTEMPTS', 'SERVERKIT_ALLOW_PRIVATE_WEBHOOKS',
            'SECRET_KEY'} <= names
