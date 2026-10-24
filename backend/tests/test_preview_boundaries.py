"""Keep preview planning pure and host effects out of its orchestration facade."""
import ast
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1] / 'app/services/previews'


def imports(text):
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ''


def forbidden(module, imported):
    if imported == 'subprocess' or imported.endswith('deployment_service'):
        return True  # shared runners/builders, never the parent-app deploy pipeline
    if module == 'plan.py':
        return imported.startswith(('flask', 'app.models', 'shutil', 'os'))
    return False


@pytest.mark.parametrize('name,ceiling', [
    ('plan.py', 100), ('source.py', 120), ('runtime.py', 200),
    ('provisioner.py', 120), ('requests.py', 120), ('lifecycle.py', 80),
])
def test_preview_owners_stay_small_and_use_existing_host_services(name, ceiling):
    text = (ROOT / name).read_text(encoding='utf-8')
    assert len(text.splitlines()) <= ceiling
    assert not [value for value in imports(text) if forbidden(name, value)]


@pytest.mark.parametrize('module,statement', [
    ('plan.py', 'from app.models import Application'),
    ('plan.py', 'import shutil'),
    ('runtime.py', 'import subprocess'),
    ('provisioner.py', 'from app.services.deployment_service import DeploymentService'),
])
def test_preview_boundary_guard_rejects_crossings(module, statement):
    assert any(forbidden(module, value) for value in imports(statement))
