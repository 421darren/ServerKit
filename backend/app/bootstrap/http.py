"""SPA delivery and consistent HTTP error responses."""
import os
from flask import request, send_from_directory
from werkzeug.exceptions import HTTPException

def register_http_handlers(app):
    # Request body size limit
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

    # JWTManager's blocklist callback enforces session validity for every JWT
    # route. MFA verification alone decodes its body token explicitly, so no
    # path-prefix exceptions can turn a pending token into a full session.

    # Serve frontend for root path
    def _spa_page():
        # Opened from ServerKit Cloud, the page is served under the relay's
        # path prefix (app/services/connect_session.py).
        from app.services import connect_session
        prefix = connect_session.tunnel_prefix(request)
        if prefix:
            return connect_session.index_under_prefix(app.static_folder, prefix)
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/')
    def serve_index():
        index = os.path.join(app.static_folder, 'index.html') if app.static_folder else None
        if index and os.path.isfile(index):
            return _spa_page()
        return {'message': 'ServerKit API is running', 'docs': '/api/v1/'}, 200

    # Expected application failures. Services raise these typed errors and the
    # HTTP boundary owns their public shape and status-code mapping.
    from app.exceptions import ApplicationError
    from app.middleware.request_id import get_request_id

    @app.errorhandler(ApplicationError)
    def application_error(e):
        request_id = get_request_id(create=True)
        app.logger.info(
            'Application error %s on %s %s [request_id=%s]: %s',
            e.code, request.method, request.path, request_id, e.message,
        )
        return e.to_dict(request_id=request_id), e.status_code

    # Unhandled exceptions. Flask only routes here when it is not propagating
    # (so pytest and the dev server still re-raise with a full traceback);
    # in production this is the difference between a logged, JSON-shaped 500 and
    # a silent Werkzeug HTML page returned to an API client that wanted JSON.
    @app.errorhandler(500)
    def internal_error(e):
        original = getattr(e, 'original_exception', None)
        exc = original or e
        # Logging, session rollback, and the error-log write live in
        # app/error_reporting.py so a route that catches Exception itself can
        # still put its crash on the record. Before that split this was the
        # only path to /monitoring/errors, so every locally-handled 500 was
        # invisible there.
        from app.error_reporting import record_unexpected, unexpected_error_body

        # JSON either way: unlike a 404, there is no sensible SPA fallback for a
        # crash, and an HTML page tells the caller nothing it can act on.
        return unexpected_error_body(record_unexpected(exc)), 500

    # Framework-generated HTTP errors (abort(), 405 from the router, 413 from
    # MAX_CONTENT_LENGTH) rendered Werkzeug's HTML page even under /api/, so an
    # API client parsing JSON got a parse error instead of the real reason.
    # The more specific 404/500 handlers above still win for those codes.
    @app.errorhandler(HTTPException)
    def http_exception(e):
        if request.path.startswith('/api/'):
            request_id = get_request_id(create=True)
            app.logger.warning(
                'HTTP %s on %s %s [request_id=%s]: %s',
                e.code, request.method, request.path, request_id, e.description,
            )
            return {
                'error': e.description or e.name,
                'status': e.code,
                'code': (e.name or 'http_error').lower().replace(' ', '_'),
                'request_id': request_id,
            }, e.code
        # Non-API paths keep Werkzeug's standard HTML error page.
        return e.get_response()

    # Catch-all route for SPA - must be after all other routes
    @app.errorhandler(404)
    def not_found(e):
        from flask import request
        if request.path.startswith('/api/'):
            return {
                'error': 'Not found',
                'status': 404,
                'code': 'not_found',
                'request_id': get_request_id(create=True),
            }, 404
        # Serve SPA index.html if it exists, otherwise JSON 404
        index = os.path.join(app.static_folder, 'index.html') if app.static_folder else None
        if index and os.path.isfile(index):
            return _spa_page()
        return {'error': 'Not found'}, 404

