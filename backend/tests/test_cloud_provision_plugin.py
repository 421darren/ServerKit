"""Cloud provisioning plugin: provider failures must not be hidden from the panel."""
import importlib.util
import os
import sys
import types

import pytest

_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'plugins', 'serverkit-cloud-provision')
_spec = importlib.util.spec_from_file_location('cloud_prov_under_test',
                                               os.path.join(_DIR, 'cloud_provisioning_service.py'))
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)
Svc = mod.CloudProvisioningService


class Resp:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body or {}
        self.text = str(self._body)

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._body

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f'HTTP {self.status_code}')


@pytest.fixture
def vultr(app):
    from app import db
    from app.models.cloud_server import CloudProvider, CloudServer
    p = CloudProvider(name='v', provider_type='vultr', api_key_encrypted='')
    db.session.add(p)
    db.session.commit()
    s = CloudServer(provider_id=p.id, name='h', external_id='abc',
                    status=CloudServer.STATUS_ACTIVE)
    db.session.add(s)
    db.session.commit()
    return p, s


def test_destroy_failure_keeps_server_active(app, vultr, monkeypatch):
    import requests
    monkeypatch.setattr(requests, 'delete', lambda *a, **k: Resp(500))
    _, s = vultr
    with pytest.raises(ValueError) as e:
        Svc.destroy_server(s.id)
    assert 'still running and billing' in str(e.value)
    from app.models.cloud_server import CloudServer
    assert CloudServer.query.get(s.id).status == CloudServer.STATUS_ACTIVE


def test_destroy_success_and_already_gone(app, vultr, monkeypatch):
    import requests
    from app.models.cloud_server import CloudServer
    _, s = vultr
    monkeypatch.setattr(requests, 'delete', lambda *a, **k: Resp(404))  # already gone
    assert Svc.destroy_server(s.id) is True
    assert CloudServer.query.get(s.id).status == CloudServer.STATUS_DESTROYED


def test_snapshot_delete_failure_keeps_row(app, vultr, monkeypatch):
    import requests
    from app import db
    from app.models.cloud_server import CloudSnapshot
    _, s = vultr
    snap = CloudSnapshot(server_id=s.id, name='n', external_id='snap1')
    db.session.add(snap)
    db.session.commit()
    monkeypatch.setattr(requests, 'delete', lambda *a, **k: Resp(403))
    with pytest.raises(ValueError):
        Svc.delete_snapshot(snap.id)
    assert CloudSnapshot.query.get(snap.id) is not None


def test_zero_ip_is_not_stored_and_refresh_fills_it(app, vultr, monkeypatch):
    import requests
    from app.models.cloud_server import CloudServer
    _, s = vultr
    s.status = CloudServer.STATUS_CREATING
    s.ip_address = None
    from app import db
    db.session.commit()
    monkeypatch.setattr(requests, 'get', lambda *a, **k: Resp(200, {'instance': {
        'main_ip': '203.0.113.7', 'v6_main_ip': ''}}))
    out = Svc.refresh_server(s.id)
    assert out.ip_address == '203.0.113.7'
    assert out.status == CloudServer.STATUS_ACTIVE


def test_real_ip_helper():
    assert mod._real_ip('0.0.0.0') is None
    assert mod._real_ip('') is None
    assert mod._real_ip(None) is None
    assert mod._real_ip('203.0.113.7') == '203.0.113.7'


def test_vultr_create_waits_for_address(app, vultr, monkeypatch):
    import requests
    import time
    p, s = vultr
    monkeypatch.setattr(time, 'sleep', lambda *_: None)
    calls = {'n': 0}

    def fake_get(*a, **k):
        calls['n'] += 1
        ip = '0.0.0.0' if calls['n'] < 3 else '203.0.113.9'
        return Resp(200, {'instance': {'id': 'abc', 'main_ip': ip}})

    monkeypatch.setattr(requests, 'get', fake_get)
    monkeypatch.setattr(requests, 'post', lambda *a, **k: Resp(202, {'instance': {
        'id': 'abc', 'main_ip': '0.0.0.0', 'monthly_cost': 5}}))
    s.name = 'new'
    s.image = 'Ubuntu 24.04'
    res = Svc._provider_create(p, s, {})
    assert res['ip_address'] == '203.0.113.9'
