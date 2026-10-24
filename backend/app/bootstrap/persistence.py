"""Database preparation and idempotent installation data upgrades."""

def prepare_persistence(app):
    from app.services.migration_service import MigrationService
    MigrationService.check_and_prepare(app)

    # Initialize default settings and migrate legacy roles
    from app.services.settings_service import SettingsService
    SettingsService.initialize_defaults()
    SettingsService.migrate_legacy_roles()
    if not app.config.get('TESTING'):
        # Size-aware retention defaults, once per install.
        # Skipped under test: the result would depend on the test host's disk.
        try:
            from app.services import storage_profile_service
            storage_profile_service.apply_to_existing()
        except Exception as e:
            app.logger.warning(f'Storage profile not applied: {e}')

    # Encrypt any legacy plaintext provider secrets at rest (idempotent —
    # DNS-provider api keys and storage credentials predate encryption).
    try:
        from app.services.dns_provider_service import DNSProviderService
        from app.services.storage_provider_service import StorageProviderService
        n_dns = DNSProviderService.encrypt_legacy_secrets()
        n_store = StorageProviderService.encrypt_legacy_secrets()
        n_settings = SettingsService.migrate_legacy_secrets()
        # Migrate DNS zones with an inline Cloudflare token onto the canonical
        # connection store (idempotent), so every zone resolves creds the same way.
        from app.services.dns_zone_service import DNSZoneService
        n_zones = DNSZoneService.link_legacy_zones()
        # Fold a legacy single-row email relay config into the unified
        # EmailProviderConnection table; idempotent, best-effort.
        try:
            from app.services.email_relay_service import EmailRelayService
            EmailRelayService.migrate_legacy_config()
        except Exception as _relay_exc:  # never block boot on this
            import logging as _logging
            _logging.getLogger(__name__).warning(
                f'Email relay legacy migration skipped: {_relay_exc}')
        if n_dns or n_store or n_settings or n_zones:
            import logging as _logging
            _logging.getLogger(__name__).info(
                f'Encrypted legacy secrets at rest: {n_dns} DNS provider(s), '
                f'{n_store} storage field(s), '
                f'{n_settings} system setting(s); linked {n_zones} DNS zone(s) '
                f'to a connection')
    except Exception as e:
        import logging as _logging
        _logging.getLogger(__name__).warning(f'Legacy secret encryption skipped: {e}')

    # Record this boot's hardware and compare it to the last one.
    # Boot is the right hook: a VPS resize requires a power-off, so the
    # change and the restart are the same event — and the in-memory spec
    # cache that used to be the only "before" value dies with the process.
    # Skipped under TESTING: create_app() runs per test session, and a
    # capture there would write rows and emit notifications into fixtures.
    if not app.config.get('TESTING'):
        try:
            from app.services import host_snapshot_service
            host_snapshot_service.record_snapshot()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'Host snapshot skipped: {e}')

    # A panel with no account yet logs its one-time setup code, so the
    # owner can read it from the service log (setup_code_service).
    if not app.config.get('TESTING'):
        try:
            from app.services import setup_code_service
            setup_code_service.ensure()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f'Setup code unavailable: {e}')
