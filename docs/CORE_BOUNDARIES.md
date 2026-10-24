# Core boundaries

## Backend application startup

`backend/app/__init__.py` owns the public `create_app`, `db`, `jwt`, `migrate`,
`limiter`, and `get_socketio` interfaces. Keep it as ordered composition.
Do not put feature initialization or worker loops back into the factory.

The assembly sequence is:

1. Configure logging and Flask extensions/request middleware
   (`bootstrap/logging.py`, `bootstrap/configuration.py`).
2. Initialize Socket.IO and the agent gateway; register core blueprints and
   restore adapters.
3. Prepare the database and installation data (`bootstrap/persistence.py`).
4. Load extensions and their compatibility upgrades (`bootstrap/plugins.py`).
5. Recover interrupted jobs, register handlers and start the runtime
   (`bootstrap/runtime.py`, `bootstrap/jobs.py`).
6. Register SPA delivery and HTTP error handlers (`bootstrap/http.py`).

Persistence, extension loading, and runtime startup execute inside the app
context. Database preparation precedes extension queries; interrupted-job
recovery precedes consumers; job handlers precede the job consumer. One-shot
Flask commands and `SERVERKIT_SKIP_BACKGROUND` suppress runtime startup.
The existing individual services retain their testing and singleton guards.
Agent heartbeat, nonce retention and anomaly retention are explicitly started
by `bootstrap/agents.py`; importing services or binding the gateway does not
launch those threads. The heartbeat runtime receives the serving Flask app.

Bootstrap may depend on services, models, middleware and jobs. Those layers
must not import bootstrap. A feature exposes a registration/initialization
function; its appropriate bootstrap phase invokes it. Existing migration
policy and fail-soft extension behavior are preserved by this split.

`backend/tests/test_bootstrap_boundaries.py` and `test_no_background_threads.py`
enforce dependency direction, factory composition, startup order, context,
worker lifecycle, and CLI suppression. The core
blueprint registry and API-error tests verify the assembled application.

## File Manager

The route in `frontend/src/pages/FileManager.jsx` composes the feature under
`components/file-manager/`. Keep the existing shared components and SCSS.

| Owner | Responsibility |
| --- | --- |
| `fileAdapter.js` | Select local/agent/S3 transport; reject unsupported operations without falling back to the local host |
| `hooks/useDirectoryBrowser.js` | URL/path navigation, history, directory loading, search and request invalidation |
| `hooks/useFileTree.js` | Tree expansion, cached child folders and target-aware refresh |
| `hooks/useFileEditor.js` | Preview reads, editable contents and save lifecycle |
| `hooks/useFileActions.js` | Folder/rename/permissions/delete actions and shared confirmation |
| `hooks/useFileTransfers.js` | Upload batches, drag/drop, progress and timer cleanup |
| `hooks/useFileSelection.js` | Selection and range-selection anchor |
| `hooks/useFileListingModel.js` | Sorting, filtering, breadcrumbs and derived counts |
| `hooks/useFilePreferences.js` | Persisted view/sidebar preferences |
| `hooks/useFileTargets.js`, `useFileVolumes.js` | Target metadata and panel volume metadata |
| `hooks/useImagePreview.js` | Thumbnail request and object-URL lifetime through the adapter |
| `FileManager*.jsx`, `FileUploadTray.jsx` | Render sections and forward user actions through props |

Add storage operations to the adapter and its explicit capability map. A
disabled button is not sufficient protection: the adapter must reject an
unsupported call. Authorization remains enforced by the backend.

Async work stays in the owning hook. Before applying a result, validate that
its request, path and target still match the current view. Keep an upload's
original destination throughout its batch. Completion must not navigate the
user back to the directory where the operation began. Failed saves retain the
draft. Thumbnails must never use the panel's local-file endpoint for an agent.

Views do not import the API service or route pages. Metadata hooks are the
documented exception to adapter-only transport: they read storage configuration,
panel version and panel volumes, not file contents. The route constructs the
adapter but does not issue API calls or await requests.

## Checks when extending these areas

- `npm run lint` in `frontend`: includes File Manager dependency/composition
  checks through `scripts/check-frontend-boundaries.mjs`.
- `npm test`: adapter contracts and positive/negative boundary-check fixtures.
- `npm run test:file-manager`: actual page in Chromium, covering navigation,
  target switching, late results, editing, confirmations and uploads.
- `npm run build`: verify the complete production import graph.
- `python -m pytest tests/test_bootstrap_boundaries.py
  tests/test_no_background_threads.py
  tests/test_core_blueprint_registry.py tests/test_cli_skips_background.py
  tests/test_api_error_shape.py` in `backend`: focused startup coverage.
- Run the full backend suite for application assembly changes.

These checks already run through the existing frontend/backend CI workflows.
Do not raise a size ceiling or allow a new dependency just to make a check pass;
first decide which existing owner should contain the behavior.
