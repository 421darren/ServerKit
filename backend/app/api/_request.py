"""Request-body parsing for routes."""
from flask import request

from app.exceptions import ValidationError


def json_object(optional=False):
    """The request body as a dict, or a 400.

    ``request.get_json()`` hands back whatever JSON was sent, so a body of
    ``null``, ``[]`` or a bare string reached ``data.get(...)`` and crashed
    the route into a 500. Flask already rejects a missing or non-JSON body
    (415/400); with ``optional=True`` that case is an empty dict instead,
    for action endpoints whose body is all optional settings.
    """
    data = request.get_json(silent=True) if optional else request.get_json()
    if data is None and optional:
        return {}
    if not isinstance(data, dict):
        raise ValidationError('Request body must be a JSON object',
                              code='validation.body_not_object')
    return data
