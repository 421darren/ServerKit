"""Tests for ClamAV plugin quarantine safety and scan argument handling."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'plugins',
                     'serverkit-clamav', 'clamav_service.py')
_spec = importlib.util.spec_from_file_location('clam_service_under_test', _PATH)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
Svc = mod.ClamAVService


@pytest.fixture
def qdir(tmp_path, monkeypatch):
    q = tmp_path / 'quarantine'
    q.mkdir()
    monkeypatch.setattr(mod.SecurityService, 'get_config',
                        classmethod(lambda cls: {'clamav': {'quarantine_path': str(q)}}))
    monkeypatch.setattr(mod.SecurityService, '_log_alert',
                        classmethod(lambda cls, *a, **k: None))
    return q


def test_quarantine_and_restore_roundtrip(qdir, tmp_path):
    f = tmp_path / 'evil.php'
    f.write_text('x')
    f.chmod(0o755)
    r = Svc.quarantine_file(str(f))
    assert r['success'], r
    assert not f.exists()
    qfile = r['quarantine_path']
    assert os.stat(qfile).st_mode & 0o777 == 0o600
    name = os.path.basename(qfile)
    r = Svc.restore_quarantined_file(name)
    assert r['success'], r
    assert f.read_text() == 'x'


@pytest.mark.parametrize('bad', ['../outside', '../quarantine-evil/x', '/etc/passwd', '..', '', 'a/b'])
def test_delete_rejects_traversal(qdir, tmp_path, bad):
    sibling = tmp_path / 'quarantine-evil'
    sibling.mkdir()
    (sibling / 'x').write_text('keep')
    (tmp_path / 'outside').write_text('keep')
    r = Svc.delete_quarantined_file(bad)
    assert r['success'] is False
    assert (sibling / 'x').exists() and (tmp_path / 'outside').exists()


@pytest.mark.parametrize('bad', ['../outside', '../quarantine-evil/x', '..', 'x.meta.json'])
def test_restore_rejects_traversal(qdir, tmp_path, bad):
    (tmp_path / 'outside').write_text('keep')
    r = Svc.restore_quarantined_file(bad)
    assert r['success'] is False


def test_restore_refuses_to_overwrite(qdir, tmp_path):
    f = tmp_path / 'a.txt'
    f.write_text('one')
    q = Svc.quarantine_file(str(f))
    f.write_text('new')
    r = Svc.restore_quarantined_file(os.path.basename(q['quarantine_path']))
    assert r['success'] is False
    assert f.read_text() == 'new'


def test_scan_file_passes_option_terminator(monkeypatch, tmp_path):
    seen = {}

    def fake(cmd, timeout=60):
        seen['cmd'] = cmd
        return {'returncode': 0, 'output': 'OK', 'success': True}

    monkeypatch.setattr(mod, 'run_checked', fake)
    monkeypatch.chdir(tmp_path)
    (tmp_path / '-rf').write_text('x')
    r = Svc.scan_file('-rf')
    assert r['success'] is True
    assert '--' in seen['cmd']
    assert seen['cmd'][-1] == str(tmp_path / '-rf')
