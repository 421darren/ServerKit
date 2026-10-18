"""
DigitalOcean provisioning from the Cloud Servers page:
- the form has no SSH key field, so the account's own SSH keys are sent
  (otherwise DigitalOcean emails a root password);
- the public IP is assigned seconds after creation, so creation waits for it
  and Refresh also works for DigitalOcean (it only handled Vultr);
- a requested agent install that did not happen is recorded, not silent.
"""
import importlib.util
import os

import pytest
import requests

_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'builtin-extensions',
                    'serverkit-cloud-provision', 'backend')
_spec = importlib.util.spec_from_file_location('cloud_prov_do_under_test',
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


NO_IP = {'droplet': {'id': 42, 'networks': {'v4': []}, 'size': {'price_monthly': 6}}}
WITH_IP = {'droplet': {'id': 42, 'networks': {'v4': [
    {'type': 'private', 'ip_address': '10.0.0.5'},
    {'type': 'public', 'ip_address': '203.0.113.7'}]}}}


@pytest.fixture
def do_api(monkeypatch):
    calls = {'post': [], 'get': []}
    state = {'polls': 0}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls['post'].append((url, json))
        return Resp(202, NO_IP)

    def fake_get(url, headers=None, timeout=None):
        calls['get'].append(url)
        if url.startswith('https://api.digitalocean.com/v2/account/keys'):
            return Resp(200, {'ssh_keys': [{'id': 111}, {'id': 222}]})
        if url == 'https://api.digitalocean.com/v2/droplets/42':
            state['polls'] += 1
            return Resp(200, WITH_IP if state['polls'] >= 2 else NO_IP)
        return Resp(404)

    monkeypatch.setattr(requests, 'post', fake_post)
    monkeypatch.setattr(requests, 'get', fake_get)
    monkeypatch.setattr('time.sleep', lambda s: None)
    monkeypatch.setattr(Svc, '_auth_headers', staticmethod(lambda provider: {}))
    return calls


@pytest.fixture
def do_provider(app):
    from app import db
    from app.models.cloud_server import CloudProvider
    p = CloudProvider(name='DigitalOcean', provider_type='digitalocean', api_key_encrypted='')
    db.session.add(p)
    db.session.commit()
    return p


def test_create_sends_account_keys_and_waits_for_ip(app, do_api, do_provider):
    srv = Svc.create_server({'provider_id': do_provider.id, 'name': 'mail.vps106.cc',
                             'region': 'fra1', 'size': 's-1vcpu-1gb',
                             'image': 'ubuntu-24-04-x64', 'install_agent': False})
    url, body = do_api['post'][0]
    assert url == 'https://api.digitalocean.com/v2/droplets'
    assert body['ssh_keys'] == [111, 222]
    assert srv.ip_address == '203.0.113.7'
    assert srv.status == 'active'


def test_explicit_key_is_used_as_given(app, do_api, do_provider):
    Svc.create_server({'provider_id': do_provider.id, 'name': 'x', 'region': 'fra1',
                       'size': 's-1vcpu-1gb', 'image': 'ubuntu-24-04-x64',
                       'ssh_key_id': 'bf:d0:bc'})
    assert do_api['post'][0][1]['ssh_keys'] == ['bf:d0:bc']
    assert not any('/account/keys' in u for u in do_api['get'])


def test_refresh_reads_ip_for_digitalocean(app, do_api, do_provider):
    from app import db
    from app.models.cloud_server import CloudServer
    s = CloudServer(provider_id=do_provider.id, name='y', external_id='42', status='creating')
    db.session.add(s)
    db.session.commit()
    Svc.refresh_server(s.id)
    Svc.refresh_server(s.id)
    s = CloudServer.query.get(s.id)
    assert s.ip_address == '203.0.113.7'
    assert s.status == 'active'


def test_skipped_agent_install_is_recorded(app, do_api, do_provider, monkeypatch):
    def boom(server):
        raise RuntimeError('ssh refused')
    monkeypatch.setattr(Svc, '_install_agent', staticmethod(boom))
    srv = Svc.create_server({'provider_id': do_provider.id, 'name': 'z', 'region': 'fra1',
                             'size': 's-1vcpu-1gb', 'image': 'ubuntu-24-04-x64',
                             'install_agent': True})
    assert srv.agent_installed is not True
    assert 'Add Server' in (srv.server_metadata or {}).get('agent_note', '')


def test_public_ipv4_helper():
    assert mod._do_public_ipv4(WITH_IP['droplet']) == '203.0.113.7'
    assert mod._do_public_ipv4(NO_IP['droplet']) is None
    assert mod._do_public_ipv4({}) is None
