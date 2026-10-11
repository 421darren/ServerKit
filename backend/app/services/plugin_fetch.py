"""Fetching extension zips: GitHub URL resolution and SSRF-guarded downloads.

Re-exported by plugin_service, which is what callers import."""
import io
import logging
import os
import re

import requests

from app.utils.env import env_bool

logger = logging.getLogger(__name__)


def _github_token():
    """Optional GitHub token (SERVERKIT_GITHUB_TOKEN). Lifts the 60/hr anonymous
    rate limit and enables private-repo installs. Never logged or echoed back."""
    return (os.environ.get('SERVERKIT_GITHUB_TOKEN') or '').strip()


def _is_github_host(url):
    """True for github.com / api.github.com / codeload.github.com URLs — the only
    hosts the token is ever attached to (never leak it to third-party mirrors,
    and never over plain http — audit L6)."""
    return bool(re.match(r'^https://(?:[a-z0-9-]+\.)?github\.com/', url or '', re.I))


def _github_api_headers(accept='application/vnd.github+json'):
    headers = {'Accept': accept, 'User-Agent': 'ServerKit-Plugin-Installer/1.0'}
    token = _github_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


class GitHubResolveError(ValueError):
    """Actionable failure resolving a GitHub URL (rate limit, 404, private)."""


def _normalize_source_url(url):
    """Accept `owner/repo` and `owner/repo@tag` shorthand, normalizing to a
    github.com URL. Full URLs and direct .zip links pass through unchanged."""
    if not url:
        return url
    u = url.strip()
    if u.startswith('http://') or u.startswith('https://') or u.endswith('.zip'):
        return u
    m = re.match(r'^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:@(.+))?$', u)
    if not m:
        return u
    owner, repo, tag = m.groups()
    if tag:
        return f'https://github.com/{owner}/{repo}/releases/tag/{tag}'
    return f'https://github.com/{owner}/{repo}'


def _resolve_github_url(url, strict=False):
    """Convert a GitHub repo URL to the latest release zip download URL.

    Handles:
      - https://github.com/user/repo  -> latest release zip
      - https://github.com/user/repo/releases/tag/v1.0.0  -> that release zip
      - Direct zip URLs pass through unchanged

    When ``strict`` is False (installs) any API hiccup silently falls back to the
    default-branch/tag zipball. When ``strict`` is True (preview) failures raise
    :class:`GitHubResolveError` with an actionable message, and a
    ``.used_zipball_fallback`` flag records whether no release asset was found.
    """
    if url.endswith('.zip'):
        return url

    # Match github.com/owner/repo patterns
    gh_match = re.match(
        r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/releases/tag/([^/]+))?/?$',
        url,
    )
    if not gh_match:
        return url

    owner, repo, tag = gh_match.groups()

    if tag:
        # Specific release - get its assets
        api_url = f'https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}'
    else:
        # Latest release
        api_url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'

    try:
        resp = requests.get(api_url, timeout=15, headers=_github_api_headers())
        if strict:
            _raise_for_github_status(resp, owner, repo)
        resp.raise_for_status()
        release = resp.json()

        # Look for a .zip asset (prefer plugin zip over source)
        for asset in release.get('assets', []):
            if asset['name'].endswith('.zip'):
                return asset['browser_download_url']

        # No .zip asset — fall back to source zipball (default branch of the tag).
        zipball = release.get('zipball_url') or (
            f'https://api.github.com/repos/{owner}/{repo}/zipball/{tag}' if tag
            else f'https://api.github.com/repos/{owner}/{repo}/zipball')
        _mark_zipball_fallback(zipball)
        return zipball
    except GitHubResolveError:
        raise
    except Exception as e:
        logger.warning(f'Could not resolve GitHub release URL: {e}')
        # Fallback: try the zipball endpoint directly (no release published).
        zipball = (f'https://api.github.com/repos/{owner}/{repo}/zipball/{tag}' if tag
                   else f'https://api.github.com/repos/{owner}/{repo}/zipball')
        _mark_zipball_fallback(zipball)
        return zipball


# Records the most recent resolution's zipball fallback so the preview flow can
# warn "no release found (installing the default-branch zipball)". Only read
# immediately after a _resolve_github_url call.
_LAST_RESOLUTION = {'zipball_fallback': False}


def _mark_zipball_fallback(_url):
    _LAST_RESOLUTION['zipball_fallback'] = True


def _raise_for_github_status(resp, owner, repo):
    """Turn a GitHub API error response into an actionable GitHubResolveError."""
    if resp.status_code == 200:
        _LAST_RESOLUTION['zipball_fallback'] = False
        return
    if resp.status_code == 403 and resp.headers.get('X-RateLimit-Remaining') == '0':
        reset = resp.headers.get('X-RateLimit-Reset')
        mins = ''
        try:
            import time as _t
            if reset:
                mins = f' (try again in ~{max(1, round((int(reset) - _t.time()) / 60))} min)'
        except Exception:
            pass
        raise GitHubResolveError(
            f'GitHub API rate limit reached{mins}. Set SERVERKIT_GITHUB_TOKEN '
            f'to raise the limit and enable private-repo installs.')
    if resp.status_code == 404:
        raise GitHubResolveError(
            f'Repository or release not found for {owner}/{repo}. Check the URL, '
            f'or set SERVERKIT_GITHUB_TOKEN if the repository is private.')
    raise GitHubResolveError(
        f'GitHub API returned HTTP {resp.status_code} for {owner}/{repo}.')


def _download_zip(url):
    """Download a zip file from URL and return bytes."""
    resolved = _resolve_github_url(url)
    return _download_resolved(resolved)


# ── Download safety (audit L4): scheme/host checks, redirect re-validation,
# and byte caps, shared by the zip and detached-signature fetches.
_MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024   # extension zip cap
_MAX_REDIRECTS = 5


def _ip_is_public(ip):
    import ipaddress
    addr = ipaddress.ip_address(ip)
    return not (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_multicast or addr.is_reserved or addr.is_unspecified)


def _assert_url_safe(url):
    """Reject anything that isn't an https URL to a public host (SSRF guard).

    Rules: https everywhere; http only for loopback dev hosts
    (http://localhost:8000/ext.zip while developing); loopback targets are
    always allowed (a same-host registry is legitimate), but RFC1918 /
    link-local / reserved targets are refused by default — a panel must never
    follow an attacker-supplied URL into the internal network or the cloud
    metadata service. Operators with a private-zone registry can opt out with
    SERVERKIT_ALLOW_PRIVATE_DOWNLOADS=1.
    """
    import ipaddress
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url or '')
    scheme = (parsed.scheme or '').lower()
    if scheme not in ('http', 'https'):
        raise ValueError(
            f"Unsupported URL scheme {scheme!r} — extension downloads must be https://")
    host = parsed.hostname
    if not host:
        raise ValueError('Download URL has no host')
    try:
        ips = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except Exception as e:
        raise ValueError(f'Could not resolve download host {host!r}: {e}')
    if all(ipaddress.ip_address(ip).is_loopback for ip in ips):
        return  # loopback dev host — http or https both fine
    if scheme == 'http':
        raise ValueError(
            'Plain-http extension downloads are only allowed for loopback dev hosts')
    if env_bool('SERVERKIT_ALLOW_PRIVATE_DOWNLOADS'):
        return
    bad = sorted(ip for ip in ips if not _ip_is_public(ip))
    if bad:
        raise ValueError(
            f'Download host {host!r} resolves to a non-public address ({bad[0]}) '
            f'— refusing to fetch (SSRF guard). Set '
            f'SERVERKIT_ALLOW_PRIVATE_DOWNLOADS=1 to allow private-zone registries.')


def _safe_get(url, timeout, headers, max_bytes):
    """GET ``url`` with per-hop SSRF re-validation (redirects are followed
    manually so each hop is re-checked), a hard byte cap, and the GitHub
    token re-computed per hop (never leaked cross-host). Returns bytes."""
    from urllib.parse import urljoin
    current = url
    for _ in range(_MAX_REDIRECTS + 1):
        _assert_url_safe(current)
        hop_headers = dict(headers or {})
        token = _github_token()
        if token and _is_github_host(current):
            hop_headers['Authorization'] = f'Bearer {token}'
        resp = requests.get(current, timeout=timeout, stream=True,
                            headers=hop_headers, allow_redirects=False)
        try:
            # status_code check rather than is_redirect: equivalent semantics,
            # and tolerant of minimal test doubles.
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get('Location')
                if not location:
                    raise ValueError('Redirect without a Location header')
                current = urljoin(current, location)
                continue
            resp.raise_for_status()
            buf = io.BytesIO()
            for chunk in resp.iter_content(chunk_size=8192):
                buf.write(chunk)
                if buf.tell() > max_bytes:
                    raise ValueError(
                        f'Download exceeds the {max_bytes // (1024 * 1024)} MB cap '
                        f'— aborting (possible zip bomb or misconfigured source)')
            buf.seek(0)
            return buf.getvalue()
        finally:
            close = getattr(resp, 'close', None)
            if callable(close):
                close()
    raise ValueError(f'Too many redirects fetching {url}')


def _download_resolved(resolved):
    """Download an already-resolved zip URL and return a BytesIO buffer."""
    logger.info(f'Downloading plugin from: {resolved}')
    headers = {
        'Accept': 'application/octet-stream',
        'User-Agent': 'ServerKit-Plugin-Installer/1.0',
    }
    data = _safe_get(resolved, timeout=120, headers=headers,
                     max_bytes=_MAX_DOWNLOAD_BYTES)
    return io.BytesIO(data)
