"""Enhanced rate limiting with per-tier limits and response headers."""
from flask import g


def get_rate_limit_key():
    """Custom key function for rate limiting based on auth context."""
    # API key auth
    api_key = getattr(g, 'api_key', None)
    if api_key:
        return f'apikey:{api_key.id}'

    # JWT auth - try to get user id
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        if user_id:
            return f'user:{user_id}'
    except Exception:
        pass

    # Fall back to the trusted client IP (ProxyFix-corrected remote_addr; never
    # a hand-parsed, client-forgeable X-Forwarded-For — see utils.client_ip).
    from app.utils.client_ip import get_client_ip
    return f'ip:{get_client_ip()}'


def _default_for_tier(tier):
    """Return default rate limit for a tier."""
    defaults = {
        'standard': '100 per minute',
        'elevated': '500 per minute',
        'unlimited': '5000 per minute',
    }
    return defaults.get(tier, '100 per minute')


def register_rate_limit_headers(app):
    """Register after_request handler to add rate limit headers."""

    @app.after_request
    def add_rate_limit_headers(response):
        # Flask-Limiter adds these headers automatically when configured,
        # but we ensure they are present with standard names
        limit = response.headers.get('X-RateLimit-Limit')
        remaining = response.headers.get('X-RateLimit-Remaining')
        reset = response.headers.get('X-RateLimit-Reset')

        if limit:
            response.headers['X-RateLimit-Limit'] = limit
        if remaining:
            response.headers['X-RateLimit-Remaining'] = remaining
        if reset:
            response.headers['X-RateLimit-Reset'] = reset

        return response
