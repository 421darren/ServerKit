"""Pure validation shared by rendering and host cache operations."""
import re


def _validate_domain(domain: str) -> bool:
    """Validate domain name to prevent nginx config injection."""
    return bool(re.match(r'^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?$', domain, re.IGNORECASE))


def _validate_path(path: str) -> bool:
    """Validate filesystem path for nginx config."""
    # Block path traversal and special characters
    if '..' in path or '\n' in path or '\r' in path or ';' in path:
        return False
    return bool(re.match(r'^/[a-zA-Z0-9/_\-\.]+$', path))
