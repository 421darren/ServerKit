"""Flask extensions, database connections, and request middleware."""
from flask_cors import CORS

def configure_application(app, db, migrate, jwt, limiter):
    # Trust the reverse proxy's forwarding headers to derive the real client IP
    # (config-gated; default off). ProxyFix rewrites request.remote_addr from the
    # rightmost TRUSTED_PROXY_HOPS entries of X-Forwarded-For — the hops our own
    # proxies appended — so a client-forged leftmost value is ignored. Applied
    # before the limiter and request handlers so every remote_addr consumer
    # (flask-limiter's get_remote_address, get_client_ip(), audit logs) benefits.
    if app.config.get('TRUST_PROXY_HEADERS'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        hops = app.config.get('TRUSTED_PROXY_HOPS', 1)
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=1, x_host=0, x_port=0)

    # Initialize extensions
    db.init_app(app)
    from app.middleware.request_profiling import register_request_profiling
    register_request_profiling(app, db)
    migrate.init_app(app, db)
    jwt.init_app(app)
    # Storage backend comes from app.config's RATELIMIT_STORAGE_URI when set
    # (see config.py); unset = in-memory, correct for the single-worker design.
    limiter.init_app(app)

    # SQLite concurrency tuning: the queue-bus consumers, job system and
    # metrics collector share one database file with request handling, and in
    # the default journal mode any writer locks the WHOLE file — readers
    # included — producing sporadic "database is locked" errors under load.
    # WAL lets readers coexist with a writer, a generous busy timeout absorbs
    # the remaining writer-writer contention, and synchronous=NORMAL is the
    # safe pairing for WAL. (journal_mode persists in the database file; the
    # per-connection pragmas re-assert it for fresh files.)
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite') and not app.config.get('TESTING'):
        # (Skipped under TESTING: tests/conftest.py owns connection pragmas
        # for the test process — journal_mode=MEMORY et al. — and two
        # listeners fighting over journal_mode on the same file deadlocks.)
        from sqlalchemy import event

        with app.app_context():
            @event.listens_for(db.engine, 'connect')
            def _sqlite_tune(dbapi_connection, _record):
                cursor = dbapi_connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA busy_timeout=30000')
                cursor.execute('PRAGMA synchronous=NORMAL')
                cursor.close()

    # Build CORS origins. Start with static config/env, then append the
    # persisted canonical domain from system settings so pointing an A record
    # at the panel works without restarting to edit .env.
    cors_origins = list(app.config['CORS_ORIGINS'])
    try:
        with app.app_context():
            from app.services.settings_service import SettingsService
            from app.utils.domain import canonical_origin
            canonical_domain = SettingsService.get('canonical_domain', '') or ''
            if canonical_domain:
                https_enabled = SettingsService.get('canonical_https_enabled', False) or False
                origin = canonical_origin(canonical_domain, https_enabled)
                if origin not in cors_origins:
                    cors_origins.append(origin)
    except Exception:
        # Database may not exist yet during first install / migrations.
        pass

    CORS(
        app,
        origins=cors_origins,
        supports_credentials=True,
        allow_headers=[
            'Content-Type', 'Authorization', 'X-Requested-With', 'X-API-Key',
            'X-Request-ID',
        ],
        expose_headers=['X-Request-ID'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        # Every panel request carries an Authorization header, which makes it a
        # non-simple cross-origin request: without Access-Control-Max-Age the
        # browser re-runs a preflight OPTIONS every few seconds (Chrome's
        # default cache is 5s), so a cross-origin panel pays two round trips per
        # call forever. One hour is the practical ceiling — Chrome caps the
        # value at 2h, Firefox at 24h, and both take the smaller of the two.
        max_age=3600,
    )

    # Assign one diagnostic ID at the outer API boundary. Downstream handlers,
    # logs and jobs can reuse g.request_id without inventing independent IDs.
    from app.middleware.request_id import register_request_id
    register_request_id(app)

    # Register security headers middleware
    from app.middleware.security import register_security_headers
    register_security_headers(app)

    # Demo mode guard — config-gated (default off), blocks mutating API calls
    from app.middleware.demo import init_demo_mode
    init_demo_mode(app)

    # Register API key authentication middleware
    from app.middleware.api_key_auth import register_api_key_auth
    register_api_key_auth(app)

    # Register API analytics middleware
    from app.middleware.api_analytics import register_api_analytics
    register_api_analytics(app)

    # Register fallback audit logging for authenticated mutating API requests
    from app.middleware.audit import register_audit_fallback
    register_audit_fallback(app)

    # Update rate limiter with custom key function
    from app.middleware.rate_limit import get_rate_limit_key, register_rate_limit_headers
    limiter._key_func = get_rate_limit_key
    register_rate_limit_headers(app)

