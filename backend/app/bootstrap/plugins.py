"""Extension installation compatibility and blueprint loading."""

def load_extensions(app):
    # Seed bundled flagship extensions (D4) — WordPress ships installed by
    # default on every panel (fresh and upgrade) unless the user uninstalled
    # it. Done BEFORE load_all_plugins so the loader registers the seeded
    # blueprints. In-place: no file copy. Best-effort.
    try:
        from app.services.plugin_service import seed_flagship_extensions
        seed_flagship_extensions()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Flagship seed: {e}')

    # Sweep files/rows of retired extensions (e.g. serverkit-workflows)
    # BEFORE the loader, so they are never loaded, never "repaired" back,
    # and never carried forward into the next update's frontend build.
    try:
        from app.services.extension_migration import remove_retired_extensions
        remove_retired_extensions()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Retired extension sweep: {e}')

    # Load installed plugins (dynamic blueprints) AFTER migrations,
    # so the installed_plugins table exists.
    try:
        from app.services.plugin_service import load_all_plugins
        load_all_plugins(app)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Plugin loader: {e}')

    # One-shot: auto-install builtin extensions that used to be core pages
    # so an upgraded panel doesn't lose the feature (decision D3). Fresh
    # installs see them in the Marketplace instead. Best-effort.
    try:
        from app.services.extension_migration import run_auto_install
        run_auto_install()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Extension auto-install: {e}')

    # Upgrade parity for the extracted security suite:
    # a panel that was actually using fail2ban/clamav/lynis/auto-updates/
    # image scanning gets the matching registry extension once its entry
    # is published. Fail-soft, retries per boot until then. Best-effort.
    try:
        from app.services.extension_migration import run_registry_auto_install
        run_registry_auto_install()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Security-suite auto-install: {e}')

    # One-shot: re-acquire the now-extracted backend for converted builtins
    # that first shipped frontend-only, so an upgraded panel
    # that installed them frontend-only doesn't lose the API. Best-effort.
    try:
        from app.services.extension_migration import run_backend_acquisition
        run_backend_acquisition()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Extension backend acquisition: {e}')

