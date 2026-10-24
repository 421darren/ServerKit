import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

from config import config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

# PyJWT 2.10+ enforces that 'sub' must be a string.
# Stringify the identity so integer user IDs work transparently.
@jwt.user_identity_loader
def _user_identity(user_id):
    return str(user_id)


@jwt.additional_claims_loader
def _session_claims(user_id):
    import time
    import secrets
    from app.models import User
    user = db.session.get(User, user_id)
    session_id = secrets.token_hex(16)
    return {'auth_version': user.auth_version if user else None,
            'session_id': session_id,
            'auth_time': int(time.time())}


@jwt.token_in_blocklist_loader
def _session_revoked(_header, claims):
    from app.middleware.session_auth import validate_session_claims
    return validate_session_claims(claims, token_type=claims.get('type')) is None


limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
# Note: key_func is updated to get_rate_limit_key after app init
socketio = None

# Path to frontend dist folder (relative to backend folder)
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist')


from app.bootstrap.logging import configure_logging as _configure_logging


def create_app(config_name=None):
    """Assemble the panel in dependency order; retain public extension exports."""
    global socketio
    from app.bootstrap.configuration import configure_application
    from app.bootstrap.persistence import prepare_persistence
    from app.bootstrap.plugins import load_extensions
    from app.bootstrap.runtime import start_runtime
    from app.bootstrap.http import register_http_handlers

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path='')
    app.config.from_object(config[config_name])
    _configure_logging(app)
    configure_application(app, db, migrate, jwt, limiter)

    # Initialize SocketIO
    from app.sockets import init_socketio
    socketio = init_socketio(app)

    # Initialize Agent Gateway
    from app.agent_gateway import init_agent_gateway
    init_agent_gateway(socketio)

    # Core routes are an explicit, ordered manifest. Extension blueprints stay
    # outside this registry and are loaded after migrations below.
    from app.core_blueprints import register_core_blueprints
    register_core_blueprints(app)

    # Register the core restore handlers after their models and API modules
    # have been imported by the blueprint registry.
    from app.services import recycle_bin_service
    recycle_bin_service.register_builtin_types()

    # Restore adapters are process-local strategy registrations. They do not
    # touch the database and must exist in testing/CLI app factories too.
    from app.services.restore_point_adapters import register_builtin_restore_point_adapters
    register_builtin_restore_point_adapters()

    with app.app_context():
        prepare_persistence(app)
        load_extensions(app)
        start_runtime(app)

    register_http_handlers(app)
    return app


def get_socketio():
    """Get the SocketIO instance."""
    return socketio
