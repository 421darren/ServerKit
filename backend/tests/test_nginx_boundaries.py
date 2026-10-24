"""Keep Nginx text generation independent of the host and the Flask app."""
import ast
from dataclasses import replace
from pathlib import Path

import pytest

from app.services.nginx import compression, rendering, templates
from app.services.nginx_service import NginxService


ROOT = Path(__file__).parents[1] / 'app' / 'services'
ALLOWED_IMPORTS = {
    '__init__.py': set(),
    'templates.py': set(),
    'validation.py': {'re'},
    'compression.py': {'re', '.templates'},
    'rendering.py': {'re', 'dataclasses', 'typing', '.templates', '.validation'},
}
RENDER_METHODS = {
    'render_site_config', '_with_wordpress_protection', '_with_immutable_assets',
    '_with_micro_cache', 'clamp_micro_cache_ttl', '_with_ssl',
    '_http_level_directives', 'render_compression_snippet',
}


def boundary_errors(filename, source):
    """Deliberately narrow dependency allowlist for this pure package."""
    tree = ast.parse(source)
    errors = []
    for node in ast.walk(tree):
        imports = []
        if isinstance(node, ast.Import):
            imports = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            prefix = '.' * node.level
            imports = ([prefix + node.module] if node.module else
                       [prefix + alias.name for alias in node.names])
        for module in imports:
            if module not in ALLOWED_IMPORTS[filename]:
                errors.append(f'forbidden dependency: {module}')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {'open', 'exec', 'eval', '__import__', 'globals', 'locals'}:
                errors.append(f'forbidden effect: {node.func.id}')
    if filename == 'templates.py':
        for node in tree.body:
            if not (isinstance(node, ast.Assign) or
                    isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)):
                errors.append('templates must contain only data')
        if any(isinstance(node, ast.Call) for node in ast.walk(tree)):
            errors.append('templates must not execute calls')
    return errors


def test_configuration_package_has_only_declared_pure_dependencies():
    paths = sorted((ROOT / 'nginx').glob('*.py'))
    assert {path.name for path in paths} == set(ALLOWED_IMPORTS)
    for path in paths:
        source = path.read_text(encoding='utf-8')
        assert boundary_errors(path.name, source) == [], path
        ceiling = 500 if path.name == 'templates.py' else 300
        assert len(source.splitlines()) <= ceiling, f'Split responsibilities in {path}'


@pytest.mark.parametrize('filename,source', [
    ('rendering.py', 'from app.services.nginx_service import NginxService'),
    ('rendering.py', 'from flask import current_app'),
    ('rendering.py', 'import os'),
    ('compression.py', 'import subprocess'),
    ('validation.py', 'from pathlib import Path'),
    ('rendering.py', "open('/etc/nginx/nginx.conf').read()"),
    ('rendering.py', "__import__('subprocess')"),
    ('templates.py', 'def render():\n    return "server {}"'),
    ('templates.py', 'CONFIG = str(123)'),
])
def test_boundary_checker_rejects_host_dependencies_and_active_templates(filename, source):
    assert boundary_errors(filename, source)


def test_service_keeps_rendering_as_delegation():
    source = (ROOT / 'nginx_service.py').read_text(encoding='utf-8')
    service = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef))
    methods = {node.name: node for node in service.body if isinstance(node, ast.FunctionDef)}
    for name in RENDER_METHODS:
        body = methods[name].body
        if isinstance(body[0], ast.Expr):
            body = body[1:]  # docstring
        assert len(body) == 1 and isinstance(body[0], ast.Return), name
        call = body[0].value
        assert isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute), name
        assert call.func.value.id in {'rendering', 'compression'}, name
        assert call.func.attr == name
    # Prevent copying templates back into the host service.
    for name in vars(templates):
        if name.isupper():
            assignment = next(node for node in service.body
                              if isinstance(node, ast.Assign)
                              and node.targets[0].id == name)
            assert isinstance(assignment.value, ast.Attribute), name
            assert assignment.value.value.id == 'templates', name
    nonblank = sum(bool(line.strip()) for line in source.splitlines())
    assert nonblank <= 1050, 'Extract additional host concerns instead of growing this service'


def test_render_settings_are_values_and_preserve_service_overrides(monkeypatch):
    monkeypatch.setattr(NginxService, 'MICROCACHE_TTL_DEFAULT', 23)
    monkeypatch.setattr(NginxService, 'MICROCACHE_TTL_MAX', 40)
    assert NginxService.clamp_micro_cache_ttl(None) == 23
    assert NginxService.clamp_micro_cache_ttl(100) == 40
    result = NginxService.render_site_config(
        'shop', 'docker', ['shop.example.com'], port=8123, micro_cache=True)
    assert 'proxy_cache_valid 200 301 23s;' in result['config']
    assert rendering.clamp_micro_cache_ttl(None) == 10  # no shared mutable state
    custom = replace(rendering.DEFAULT_SETTINGS, MICROCACHE_TTL_DEFAULT=17)
    assert rendering.clamp_micro_cache_ttl(None, settings=custom) == 17


def test_compression_service_preserves_directive_overrides(monkeypatch):
    monkeypatch.setattr(NginxService, 'GZIP_DIRECTIVES', (('gzip', 'off'),))
    actual = NginxService.render_compression_snippet('', '/ours.conf')
    assert 'gzip off;' in actual and 'gzip_types' not in actual
    assert 'gzip on;' in compression.render_compression_snippet('', '/ours.conf')


@pytest.mark.parametrize('kwargs,error', [
    ({'domains': []}, 'At least one domain'),
    ({'domains': ['_']}, 'reserved'),
    ({'domains': ['shop.example.com; include /tmp/evil']}, 'Invalid domain'),
    ({'root_path': '/srv/../etc'}, 'Invalid root'),
    ({'root_path': '/srv/shop\ninclude /tmp/evil'}, 'Invalid root'),
    ({'port': None}, 'need a port'),
    ({'app_type': 'unknown'}, 'Unknown service type'),
])
def test_pure_rendering_preserves_input_rejection(kwargs, error):
    args = dict(name='shop', app_type='docker', domains=['shop.example.com'], port=8123)
    args.update(kwargs)
    result = rendering.render_site_config(**args)
    assert result['success'] is False
    assert error in result['error']
