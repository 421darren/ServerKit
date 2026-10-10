"""One per-app loader replaces nine copies.

Each copy loaded the live app and checked access, but they disagreed on
the answer for a denied caller, on return shapes, and on docstrings that
promised error tuples while the code raised. ``get_app_for`` keeps each
surface's choice explicit: 403 for a denied caller, or the same 404 as a
missing app with ``conceal``.
"""
import pytest

from app.exceptions import NotFoundError, PermissionDeniedError
from app.services.resource_grant_service import ResourceGrantService
from factories import make_application, make_user


@pytest.fixture
def people(app):
    from app import db
    owner = make_user(db, 'ra_owner')
    viewer = make_user(db, 'ra_viewer')
    stranger = make_user(db, 'ra_stranger')
    admin = make_user(db, 'ra_admin', 'admin')
    application = make_application(db, name='ra-app', user_id=owner.id)
    ResourceGrantService.grant(viewer.id, 'application', application.id, role='viewer')
    return {'owner': owner, 'viewer': viewer, 'stranger': stranger,
            'admin': admin, 'app': application}


def get(user, app_id, **kw):
    return ResourceGrantService.get_app_for(user, app_id, **kw)


def test_missing_app_is_404(people):
    with pytest.raises(NotFoundError):
        get(people['admin'], 999999)


def test_denied_caller_is_403_or_a_concealed_404(people):
    app_id = people['app'].id
    with pytest.raises(PermissionDeniedError):
        get(people['stranger'], app_id)
    with pytest.raises(NotFoundError):
        get(people['stranger'], app_id, conceal=True)


def test_viewer_grant_reads_but_cannot_write(people):
    app_id = people['app'].id
    assert get(people['viewer'], app_id).id == app_id
    with pytest.raises(PermissionDeniedError):
        get(people['viewer'], app_id, write=True)


def test_owner_and_admin_write(people):
    app_id = people['app'].id
    assert get(people['owner'], app_id, write=True).id == app_id
    assert get(people['admin'], app_id, write=True).id == app_id


def test_no_user_is_denied(people):
    with pytest.raises(PermissionDeniedError):
        get(None, people['app'].id)
