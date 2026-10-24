"""Fleet worker threads run inside the live app, never a fresh create_app().

A per-thread create_app() reran migrations and plugin loading, rebound
Socket.IO and ran the boot reconcile against the live panel. The upgrade
fan-out had the opposite bug: no app context at all, so its first query
raised and online agents were never told to upgrade.
"""
import threading
from unittest.mock import patch

import pytest
from flask import current_app, has_app_context

from factories import make_server


@pytest.fixture
def calls(app):
    """Record each dispatch from whatever thread makes it."""
    seen, done = [], threading.Event()

    def fake_send(**kwargs):
        seen.append({'context': has_app_context(),
                     'app': current_app._get_current_object() if has_app_context() else None,
                     'action': kwargs['action']})
        done.set()
        return {'success': True, 'data': {}}

    def no_new_app(*a, **k):
        raise AssertionError('fleet thread built a second app')

    with patch('app.services.remote_command_dispatcher.agent_registry.send_command',
               side_effect=fake_send), patch('app.create_app', side_effect=no_new_app):
        yield seen, done


def test_upgrade_dispatch_runs_in_the_live_app(app, calls):
    from app import db
    from app.models.server import AgentVersion
    from app.services.agent_fleet_service import fleet_service
    seen, done = calls
    server = make_server(db, name='ft-online', status='online',
                         os_type='linux', architecture='amd64')
    version = AgentVersion(version='9.9.9', assets={'linux-amd64': 'https://x/a'})
    db.session.add(version)
    db.session.commit()

    result = fleet_service.upgrade_servers([server.id], version.id)

    assert result['results'][0]['success'], result
    assert done.wait(10)
    assert seen == [{'context': True, 'app': app, 'action': 'agent:update'}]


def test_queued_delivery_runs_in_the_live_app(app, calls):
    from app import db
    from app.models.server import ServerCommand
    from app.services.agent_fleet_service import fleet_service
    seen, done = calls
    server = make_server(db, name='ft-queued')
    cmd = fleet_service.queue_command(server.id, 'agent:update', {})

    fleet_service.deliver_queued_commands(server.id)

    assert done.wait(10)
    assert seen[0]['context'] and seen[0]['app'] is app
    for _ in range(50):  # the thread commits after dispatch returns
        db.session.expire_all()
        if db.session.get(ServerCommand, cmd.id).status == 'completed':
            break
        threading.Event().wait(0.1)
    assert db.session.get(ServerCommand, cmd.id).status == 'completed'
