"""Process-local agent maintenance starts only in the server runtime."""


def start_agent_runtime(app):
    if app.config.get('TESTING'):
        return

    from app.services.agent_registry import agent_registry
    from app.services.nonce_service import nonce_service
    from app.services.anomaly_detection_service import anomaly_detection_service

    agent_registry.start(app)
    nonce_service.start_cleanup()
    anomaly_detection_service.start_cleanup()
