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

## Nginx configuration generation

`backend/app/services/nginx_service.py` remains the compatible host-facing
interface. It owns file updates, config testing, reloads, rollback and restore
checkpoints. Configuration generation lives under `services/nginx/`:

| Owner | Responsibility |
| --- | --- |
| `templates.py` | Configuration text and default values, with no executable behavior |
| `validation.py` | Domain/path validation shared by rendering and cache operations |
| `rendering.py` | Vhost selection, immutable assets, micro-cache, WordPress protection and SSL wrapping |
| `compression.py` | Compression directives computed from supplied nginx dump/version text |

The dependency direction is host service → pure configuration modules →
templates/validation. Rendering never imports Flask, models, other services,
filesystem APIs or process runners. It accepts values and returns text or an
error. `RenderSettings` is an immutable value object; the compatibility service
copies its template settings into that object, preserving class-level settings
without passing the service itself into the renderer. Compression similarly
receives directive tuples. Keep privileged writes and reloads in the existing
host lifecycle; a rendering feature must not create another write path.

The old `NginxService` methods and template attributes remain available. New
rendering behavior belongs in the pure modules; those service methods must stay
delegates. `test_nginx_boundaries.py` enforces that direction, data-only templates
and module size limits, with negative fixtures for forbidden dependencies.
`test_nginx_render_contract.py` captures 512 pre-extraction rendering combinations.
Its digests are a refactoring contract: change them only for an intentional
output change backed by semantic tests and, where relevant, real nginx parsing.

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
- Nginx changes: run `test_nginx_boundaries.py`, `test_nginx_render_contract.py`
  and the existing nginx, micro-cache, immutable-assets, HTTPS, WordPress
  protection and restore-point tests. On Linux with nginx installed, run
  `SERVERKIT_REAL_BINARIES=1 python -m pytest tests/test_real_nginx_vhost_syntax.py`
  to validate generated configuration with the actual nginx parser.

These checks already run through the existing frontend/backend CI workflows.
Do not raise a size ceiling or allow a new dependency just to make a check pass;
first decide which existing owner should contain the behavior.


## Effective environment and preview truthfulness

`EnvService._effective_entries` owns the shared/local merge used by both
single-container and per-service Compose deployment, and by the read-only
`GET /api/v1/apps/<id>/env?view=effective&service=<name>` projection. Preserve
workspace → project → environment → attached group → local precedence and
filter service targets before merging. Shared interpolation precedes local
overrides, as in the existing deployment path.

The effective view is managed configuration for the next deploy/restart, not
an inspection of the running container or of image/Compose-file defaults.
Its explicit field allowlist excludes **all values**, including non-secret
variables that could interpolate a secret. Local references are not resolved
for this view. Existing app access checks apply; `mask=false` cannot enable
values. A shared-resolution failure returns `complete: false`, with local
rows only. Do not present that fallback as complete configuration.

`components/environment/EnvironmentPanel` composes the existing local editor
with `EffectiveEnvironment`. The view renders provenance; the hook owns service
discovery, fetching and stale-response suppression. Keep precedence on the
backend. A service-discovery request failure must not silently fall back to
unfiltered winners. The existing discovery endpoint returns an empty list for
both non-Compose apps and unreadable Compose files, so that case is explicitly
labelled as unfiltered configuration.

A preview can be advertised as running only after an explicit successful
provider result with runtime IDs. Generic manifest configuration generation is
not deployment and reports `unavailable`. Legacy running rows without IDs are
projected as unavailable without mutating them on read. Only running previews
with recorded IDs expose a URL. These checks establish provisioning evidence;
they do not claim live container health or validate DNS reachability.

Regression coverage: `test_effective_env.py`, `test_env_vars_api.py`,
`test_compose_env_overlay.py`, `test_previews.py`, and
`node scripts/effective-environment-browser.mjs` (in `frontend`). The browser
check runs in frontend CI and covers service switching with late replies,
failed discovery, masking, incomplete results, retry, the local editor, and
preview link/toast behavior.
