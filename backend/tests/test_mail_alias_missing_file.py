"""
A fresh docker-mailserver has no postfix-virtual.cf until the first alias is
created. Listing aliases must then return an empty list, not an error, for
both local and remote (agent) servers. The remote agent reports the message
in stdout or a combined output field rather than stderr, which the old check
missed, so the Mail page showed "Failed to list aliases" for a new server.
"""
import pytest

from app.services import mail_server_service as mss
from app.services.mail_server_service import MailServerService

MSG = ("2026-10-17 19:03:25+00:00 \x1b[1;31mERROR\x1b[0m listalias: "
       "'/tmp/docker-mailserver/postfix-virtual.cf' does not exist")

EMPTY = ("\x1b[1;31mERROR\x1b[0m listalias: "
         "'/tmp/docker-mailserver/postfix-virtual.cf' is empty, nothing to list")


def _fake(monkeypatch, result):
    monkeypatch.setattr(mss.RemoteDockerService, 'exec_command',
                        staticmethod(lambda **kw: result))


@pytest.mark.parametrize('result', [
    {'success': True, 'data': {'stdout': MSG, 'stderr': '', 'exit_code': 1}},   # remote: stdout
    {'success': True, 'data': {'output': MSG, 'exit_code': 1}},                 # remote: combined
    {'success': False, 'error': MSG},                                          # agent error
    {'success': False, 'error': MSG, 'data': {'stderr': MSG, 'exit_code': 1}},  # local exec
    {'success': True, 'data': {'stdout': '', 'stderr': MSG, 'exit_code': 1}},   # stderr
    {'success': True, 'data': {'stdout': EMPTY, 'exit_code': 1}},               # empty file
])
def test_missing_alias_file_is_an_empty_list(monkeypatch, result):
    _fake(monkeypatch, result)
    assert MailServerService.list_aliases(server_id='srv') == {
        'success': True, 'aliases_raw': ''}


def test_real_failure_is_still_reported(monkeypatch):
    _fake(monkeypatch, {'success': True,
                        'data': {'stdout': '', 'stderr': 'container not running',
                                 'exit_code': 1}})
    r = MailServerService.list_aliases(server_id='srv')
    assert r['success'] is False
    assert 'container not running' in r['error']


def test_agent_failure_is_passed_through(monkeypatch):
    _fake(monkeypatch, {'success': False, 'error': 'agent offline'})
    assert MailServerService.list_aliases(server_id='srv') == {
        'success': False, 'error': 'agent offline'}


def test_aliases_listed_normally(monkeypatch):
    _fake(monkeypatch, {'success': True,
                        'data': {'stdout': '* info@x.cc a@x.cc', 'exit_code': 0}})
    assert MailServerService.list_aliases(server_id='srv') == {
        'success': True, 'aliases_raw': '* info@x.cc a@x.cc'}


def _framed(text, stream=1):
    b = text.encode()
    return (bytes([stream, 0, 0, 0]) + len(b).to_bytes(4, 'big')).decode('latin-1') + text


def test_docker_stream_headers_and_colors_are_stripped(monkeypatch):
    """The remote agent returned the raw multiplexed exec stream, so every
    line started with an invisible 8-byte header and the page parsed 0
    mailboxes / 0 aliases although both existed."""
    raw = (_framed('* postmaster@vps106.cc ( 2.0K / ~ ) [0%]\r\n')
           + _framed('    [ aliases -> abuse@vps106.cc ]\r\n'))
    _fake(monkeypatch, {'success': True, 'data': {'stdout': raw, 'exit_code': 0}})
    r = MailServerService.list_mailboxes(server_id='srv')
    assert r['mailboxes_raw'].splitlines()[0] == '* postmaster@vps106.cc ( 2.0K / ~ ) [0%]'

    _fake(monkeypatch, {'success': True, 'data': {
        'stdout': _framed('\x1b[0;32m* abuse@vps106.cc postmaster@vps106.cc\x1b[0m\n'),
        'exit_code': 0}})
    assert MailServerService.list_aliases(server_id='srv')['aliases_raw'] == \
        '* abuse@vps106.cc postmaster@vps106.cc\n'


def test_plain_output_is_unchanged(monkeypatch):
    raw = '* a@x.cc ( 0 / ~ ) [0%]\n'
    _fake(monkeypatch, {'success': True, 'data': {'stdout': raw, 'exit_code': 0}})
    assert MailServerService.list_mailboxes(server_id='srv')['mailboxes_raw'] == raw
