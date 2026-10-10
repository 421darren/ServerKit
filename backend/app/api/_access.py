"""Per-app access for routes: the one way a view loads "the app this caller
may touch". Raises the typed 404/403 the global error handler renders."""
from flask import request

from app.services.resource_grant_service import ResourceGrantService
from app.services.workspace_service import WorkspaceService
from app.middleware.rbac import get_current_user


def require_app(app_id, *, write=False, conceal=False):
    """The live application the current user may read, or edit with ``write``.

    ``conceal`` answers a denied caller with the same 404 as a missing app.
    """
    return ResourceGrantService.get_app_for(
        get_current_user(), app_id, write=write, conceal=conceal)


def visible_workspace_ids(user):
    """Workspace ids the caller may see, honouring the active workspace
    context (``X-Workspace-Id`` header or ``workspace_id`` query param)."""
    requested = request.headers.get('X-Workspace-Id') or request.args.get('workspace_id')
    return WorkspaceService.visible_workspace_ids(
        user, WorkspaceService.resolve_workspace_id(user, requested))
