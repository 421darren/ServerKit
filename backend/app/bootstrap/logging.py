"""Process-wide logging configuration."""
import os
import sys

# Set once per process: create_app() runs many times in a test session and
# gunicorn imports the module before forking, so an unguarded addHandler would
# duplicate every log line N times.
_logging_configured = False


def configure_logging(app):
    """Give the app a real logging setup.

    Services across the codebase call ``logging.getLogger(__name__).warning(...)``
    but nothing ever configured the root logger, so those records fell through to
    logging's last-resort handler: WARNING and above only, no timestamp, no
    logger name, INFO dropped on the floor. That is why a panel that was failing
    to serve its own agent installer (issue #101) produced no diagnostic trail at
    all. ``LOG_LEVEL`` overrides the default.
    """
    global _logging_configured

    import logging

    level_name = os.environ.get('LOG_LEVEL', '').upper()
    if level_name and hasattr(logging, level_name):
        level = getattr(logging, level_name)
    elif app.config.get('TESTING'):
        # TestingConfig sets DEBUG=True, so keying off DEBUG alone would move the
        # whole test suite to DEBUG logging as a side effect of adding a handler.
        level = logging.INFO
    else:
        level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO

    from flask.logging import default_handler

    root = logging.getLogger()
    root.setLevel(level)
    app.logger.setLevel(level)

    # Flask attaches its own handler to app.logger, which ALSO propagates to the
    # root logger. Leaving both in place prints every app.logger record twice --
    # once as Flask's `%(module)s` and once as ours as `%(name)s`. Drop Flask's
    # and let the single root handler below own the output.
    app.logger.removeHandler(default_handler)

    if not _logging_configured:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        ))
        root.addHandler(handler)
        _logging_configured = True
