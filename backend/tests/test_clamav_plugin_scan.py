"""Directory-scan result parsing for the ClamAV plugin."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'plugins',
                     'serverkit-clamav', 'clamav_service.py')
_spec = importlib.util.spec_from_file_location('clam_service_scan_test', _PATH)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
Svc = mod.ClamAVService


@pytest.fixture(autouse=True)
def quiet(monkeypatch, tmp_path):
    monkeypatch.setattr(mod.SecurityService, 'get_config',
                        classmethod(lambda cls: {'clamav': {'quarantine_path': str(tmp_path / 'q')}}))
    for name in ('_log_scan', '_log_alert', '_send_security_notification'):
        monkeypatch.setattr(mod.SecurityService, name, classmethod(lambda cls, *a, **k: None))


def _run(monkeypatch, tmp_path, output, returncode):
    seen = {}

    def fake(cmd, timeout=60):
        seen['cmd'] = cmd
        return {'returncode': returncode, 'output': output, 'success': returncode == 0}

    monkeypatch.setattr(mod, 'run_checked', fake)
    Svc._current_scan = {'status': 'running', 'files_scanned': 0, 'infected_files': [], 'errors': []}
    Svc._run_directory_scan(str(tmp_path), True)
    return Svc._current_scan, seen['cmd']


def test_counts_files_and_parses_infected_path_with_colon(monkeypatch, tmp_path):
    out = ("/srv/a: b/x.php: Php.Webshell-1 FOUND\n\n----------- SCAN SUMMARY -----------\n"
           "Scanned files: 42\nInfected files: 1\n")
    scan, cmd = _run(monkeypatch, tmp_path, out, 1)
    assert scan['status'] == 'completed'
    assert scan['files_scanned'] == 42
    assert scan['infected_files'] == ['/srv/a: b/x.php']
    assert '--no-summary' not in cmd and '--' in cmd


def test_clean_scan(monkeypatch, tmp_path):
    scan, _ = _run(monkeypatch, tmp_path, "Scanned files: 7\nInfected files: 0\n", 0)
    assert scan['status'] == 'completed' and scan['infected_files'] == []
    assert scan['files_scanned'] == 7


@pytest.mark.parametrize('rc', [2, None])
def test_scanner_failure_is_not_reported_as_completed(monkeypatch, tmp_path, rc):
    scan, _ = _run(monkeypatch, tmp_path, "ERROR: Can't open directory\n", rc)
    assert scan['status'] == 'error'
    assert 'Can' in scan['error']
