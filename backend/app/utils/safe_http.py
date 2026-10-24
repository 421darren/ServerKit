"""Outbound HTTP to URLs that users configure (webhooks, notification hooks).

A URL a developer types in is a request the panel makes from inside the
network: to its own API on loopback, to other hosts on the LAN, or to the
cloud metadata service. :func:`post` refuses those targets, connects to the
exact address it checked (so a DNS answer can't change between the check
and the connect), never follows redirects, and caps the response body it
keeps. ``SERVERKIT_ALLOW_PRIVATE_WEBHOOKS=1`` lifts the address rule for
operators who deliberately forward to internal hosts.
"""
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter

from app.utils.env import env_bool

ALLOW_PRIVATE_ENV = 'SERVERKIT_ALLOW_PRIVATE_WEBHOOKS'
MAX_RESPONSE_BYTES = 64 * 1024


class UnsafeURLError(ValueError):
    """The URL points somewhere the panel must not send requests."""


def _is_public(addr):
    if addr.version == 6 and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return addr.is_global and not addr.is_multicast


def resolve_public(url):
    """Validate *url* and return ``(parts, ip)`` — the address to connect to.

    Raises :class:`UnsafeURLError` for a non-http(s) URL, an unresolvable
    host, or a host with any non-public address.
    """
    parts = urlsplit(url or '')
    if parts.scheme not in ('http', 'https'):
        raise UnsafeURLError('URL must start with http:// or https://')
    host = parts.hostname
    if not host:
        raise UnsafeURLError('URL has no host')
    try:
        port = parts.port or (443 if parts.scheme == 'https' else 80)
    except ValueError:
        raise UnsafeURLError('URL has an invalid port')
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as exc:
        raise UnsafeURLError(f'Could not resolve {host}: {exc}')
    addrs = [ipaddress.ip_address(info[4][0].split('%')[0]) for info in infos]
    if not addrs:
        raise UnsafeURLError(f'Could not resolve {host}')
    if not env_bool(ALLOW_PRIVATE_ENV):
        blocked = [a for a in addrs if not _is_public(a)]
        if blocked:
            raise UnsafeURLError(
                f'{host} resolves to a non-public address ({blocked[0]}); set '
                f'{ALLOW_PRIVATE_ENV}=1 to allow internal targets')
    return parts, addrs[0]


class _PinnedAdapter(HTTPAdapter):
    """Keeps TLS SNI and certificate checks on the hostname while the socket
    goes to the pre-resolved IP in the URL."""

    def __init__(self, hostname, **kwargs):
        self._hostname = hostname
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['server_hostname'] = self._hostname
        kwargs['assert_hostname'] = self._hostname
        super().init_poolmanager(*args, **kwargs)


def post(url, *, timeout=10, max_bytes=MAX_RESPONSE_BYTES, headers=None, **kwargs):
    """``requests.post`` to a public address only; see the module docstring.

    The returned response's body is truncated to *max_bytes*.
    """
    parts, ip = resolve_public(url)
    ip_host = f'[{ip}]' if ip.version == 6 else str(ip)
    netloc = ip_host if parts.port is None else f'{ip_host}:{parts.port}'
    pinned = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    host_header = parts.hostname if parts.port is None else f'{parts.hostname}:{parts.port}'
    headers = {**(headers or {}), 'Host': host_header}

    with requests.Session() as session:
        if parts.scheme == 'https':
            session.mount('https://', _PinnedAdapter(parts.hostname))
        resp = session.post(pinned, headers=headers, timeout=timeout,
                            allow_redirects=False, stream=True, **kwargs)
        try:
            resp._content = resp.raw.read(max_bytes, decode_content=True)
        finally:
            resp.close()
    return resp
