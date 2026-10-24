"""Render compression directives from supplied nginx dump/version text."""
import re

from . import templates


def _http_level_directives(dump: str, skip_file: str) -> set:
    """Directive names set at http level in an ``nginx -T`` dump.

    ``nginx -T`` prints each file after a ``# configuration file <path>:``
    header. In the main nginx.conf, http level is depth 1 inside
    ``http {}``; every other file is included from the http block (conf.d)
    or a server (sites), so its depth-0 directives are the http-level
    ones. ``skip_file`` (our own snippet) is ignored so a rewrite never
    mistakes its own lines for someone else's.
    """
    found = set()
    current = None
    depth = 0
    in_http = False
    for raw in dump.splitlines():
        header = re.match(r'^# configuration file (.+):$', raw.strip())
        if header:
            current = header.group(1)
            depth = 0
            in_http = False
            continue
        if current is None or current == skip_file:
            continue
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        is_main = current.endswith('/nginx.conf')
        http_level = (depth == 1 and in_http) if is_main else depth == 0
        name = line.split(None, 1)[0].rstrip(';{')
        if http_level and line.endswith(';'):
            found.add(name)
        if is_main and depth == 0 and name == 'http' and '{' in line:
            in_http = True
        depth += line.count('{') - line.count('}')
        if is_main and depth == 0:
            in_http = False
    return found


def render_compression_snippet(dump: str, conf_path: str,
                               nginx_v: str = '', *, gzip_directives=templates.GZIP_DIRECTIVES, brotli_directives=templates.BROTLI_DIRECTIVES) -> str:
    """The snippet for this box. When the running config already sets
    everything it is comments only: still written, so the "already
    handled" check stays a file-exists test instead of an ``nginx -T``
    on every vhost write."""
    present = _http_level_directives(dump, conf_path)
    brotli = ('ngx_http_brotli_filter_module' in dump
              or 'brotli' in (nginx_v or '').lower())
    wanted = list(gzip_directives)
    if brotli:
        wanted += list(brotli_directives)
    lines = [f'{name} {value};' for name, value in wanted if name not in present]
    kept = sorted(name for name, _ in wanted if name in present)
    header = ['# ServerKit compression (auto-generated; do not edit).']
    if kept:
        header.append('# Already set elsewhere, left alone: ' + ', '.join(kept))
    return '\n'.join(header + lines) + '\n'
