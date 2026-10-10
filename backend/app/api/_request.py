"""Request-body parsing for routes."""
from flask import request

from app.exceptions import ValidationError


def json_object():
    """The request body as a dict, or a 400.

    ``request.get_json()`` hands back whatever JSON was sent, so a body of
    ``null`` or ``[]`` reached ``data.get(...)`` and crashed the route into a
    500. Empty and non-JSON bodies are already rejected by Flask.
    """
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValidationError('Request body must be a JSON object',
                              code='validation.body_not_object')
    return data
