"""Observe-mode enforcement — the read/write matrix (plan 27 Phase 4, #9/#10).

Decision 5: an Observed server keeps reads (metrics, doctor probes, survey,
file/list reads) but every mutating server-targeted command is refused at the
single choke point (``agent_registry.send_command``). This proves the classifier
and that the guard actually blocks writes while letting reads through.

Reconstructed from the clean recovery pyc
(``test_observe_enforcement.cpython-311-pytest-9.0.3.pyc``).
"""
import hashlib
import hmac
import time

import pytest

from app import db as _db
from app.models.server import Server
from app.services.agent_registry import agent_registry

# Observe-mode enforcement is active again at the single command choke point.
# Keep this matrix as the contract: reads pass, mutations are refused.

CONNECT = '/api/v1/agent/connect'

# (action, is_read) — the classifier's whole contract, one row per class of
# command the panel routes to an agent.
ACTION_MATRIX = [
    ('system:metrics', True),
    ('system:info', True),
    ('system:processes', True),
    ('docker:container:list', True),
    ('docker:image:list', True),
    ('docker:compose:ps', True),
    ('file:read', True),
    ('file:list', True),
    ('survey:read', True),
    ('doctor:probe', True),
    ('agent:recapabilities', True),
    ('docker:container:start', False),
    ('docker:container:restart', False),
    ('docker:container:delete', False),
    ('docker:image:pull', False),
    ('docker:compose:up', False),
    ('systemd:restart', False),
    ('cron:update', False),
    ('file:write', False),
    ('cron:create', False),
    ('nginx:sites:create', False),
]


def test_is_read_action_classifies_every_class():
    for action, is_read in ACTION_MATRIX:
        assert Server.is_read_action(action) is is_read, action


def test_is_read_action_defaults_to_write_when_unknown():
    assert Server.is_read_action('mystery:frobnicate') is False
    assert Server.is_read_action('') is False
    assert Server.is_read_action(None) is False


def _connect_agent(client, monkeypatch):
    """Register a connected poll-mode agent and return its server_id."""
    api_key, api_secret = Server.generate_api_credentials()
    server = Server(name='observed-e2e', agent_id='agent-obs')
    server.set_api_key(api_key)
    server.permissions = ['*']
    _db.session.add(server)
    _db.session.commit()
    server_id = server.id

    monkeypatch.setattr(Server, 'get_api_secret', lambda self: api_secret)

    ts = int(time.time() * 1000)
    nonce = 'nonce-obs-1'
    msg = f'{server.agent_id}:{ts}:{nonce}'
    sig = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    resp = client.post(CONNECT, json={
        'agent_id': server.agent_id,
        'api_key_prefix': server.api_key_prefix,
        'signature': sig,
        'timestamp': ts,
        'nonce': nonce,
    })
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return server_id


def _set_mode(server_id, mode):
    server = Server.query.get(server_id)
    server.management_mode = mode
    _db.session.commit()


def test_observed_refuses_mutations_allows_reads(app, client, monkeypatch):
    server_id = _connect_agent(client, monkeypatch)
    _set_mode(server_id, 'observed')

    for action, is_read in ACTION_MATRIX:
        result = agent_registry.send_command(server_id, action, params={},
                                             timeout=0.3)
        if is_read:
            # Reads pass the observe guard (they only fail later on the absent
            # agent transport — never with the read-only refusal).
            assert result.get('code') != 'OBSERVED_READONLY', action
        else:
            assert result.get('code') == 'OBSERVED_READONLY', action
            assert result.get('success') is False, action


def test_observed_break_glass_allows_agent_update(app, client, monkeypatch):
    server_id = _connect_agent(client, monkeypatch)
    server = Server.query.get(server_id)
    server.management_mode = 'observed'
    server.allow_agent_update_observed = True
    _db.session.commit()

    result = agent_registry.send_command(server_id, 'agent:update', params={}, timeout=0.3)
    assert result.get('code') != 'OBSERVED_READONLY'


def test_managed_allows_mutations_past_guard(app, client, monkeypatch):
    server_id = _connect_agent(client, monkeypatch)
    _set_mode(server_id, 'managed')

    # A managed server never trips the observe guard — the mutating command
    # flows past it (and only then fails on the stubbed transport).
    result = agent_registry.send_command(server_id, 'docker:container:restart',
                                         params={}, timeout=0.3)
    assert result.get('code') != 'OBSERVED_READONLY'
