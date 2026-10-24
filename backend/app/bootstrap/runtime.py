"""Background runtime startup; skipped for one-shot CLI invocations."""
import os
import sys

def start_runtime(app):
    # Background daemons (metrics collector, queue consumers, analytics
    # flush, the job system, the linked-panel client) only make sense in a
    # long-running server process. When the app is loaded by a Flask CLI
    # one-shot — crucially `flask db upgrade` during an update — they must
    # NOT start: they query the database before migrations have run, and
    # any failure there (a corrupt DB, or pre-migration schema the new code
    # doesn't match yet) aborts the CLI command and sinks the whole update.
    # SERVERKIT_SKIP_BACKGROUND=1 forces the same skip; the updater sets it
    # as an explicit contract when running migrations.
    _cli_one_shot = (
        os.path.basename(sys.argv[0] or '').startswith('flask')
        and (len(sys.argv) < 2 or sys.argv[1] != 'run')
    )
    from app.utils.env import env_bool
    _skip_background = env_bool('SERVERKIT_SKIP_BACKGROUND') or _cli_one_shot
    if not _skip_background:
        # Before any consumer polls: release what the previous process
        # left in flight, or it stays stranded forever.
        if not app.config.get('TESTING'):
            from app.jobs.service import JobService
            try:
                JobService.recover_interrupted()
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Interrupted-job recovery failed')

        # Start metrics history collection in background
        from app.services.metrics_history_service import MetricsHistoryService
        if not MetricsHistoryService.is_running():
            MetricsHistoryService.start_collection(app)

        # Start queue-bus webhook consumer
        from app.queue_bus.consumers import start_webhook_consumer
        start_webhook_consumer(app)

        # Start queue-bus notification consumer (delivers in-app/email/chat)
        from app.notifications.consumer import start_notification_consumer
        start_notification_consumer(app)

        # Start the API analytics flush thread (a 5s buffer flush — a real-time
        # stream, deliberately NOT modeled as a job).
        from app.middleware.api_analytics import start_analytics_flush_thread
        start_analytics_flush_thread(app)

        # Start the unified job system: ONE consumer runs every enqueued Job and
        # ONE scheduler ticks all periodic work. This supersedes the former set
        # of per-domain daemon scheduler threads (auto-sync, snapshot-retention,
        # workflow, health-check, wp-update, api-background, pairing-prune,
        # registrar-expiry) — they are now ScheduledJob rows backed by the
        # built-in handlers in app/jobs/builtin_handlers.py.
        from app.jobs import start_job_system
        from app.bootstrap.jobs import register_job_handlers
        seed_builtin_schedules = register_job_handlers(app)
        start_job_system(app, seed=seed_builtin_schedules)

        # Threshold alerting and the uptime sampler are switched on from
        # the UI; without this they silently stop at the next restart
        # while their status still reads "enabled".
        # Best effort: a resume failure must never stop the panel booting.
        if not app.config.get('TESTING'):
            from app.services.monitoring_service import MonitoringService
            from app.services.uptime_service import UptimeService
            for resume in (lambda: MonitoringService.resume_if_enabled(app),
                           UptimeService.resume_if_enabled):
                try:
                    resume()
                except Exception:  # noqa: BLE001
                    app.logger.exception('Could not resume a background monitor at boot')

        # Resume the embedded agent when this panel is linked to a master
        # ServerKit panel (ServerKit-to-ServerKit peering).
        from app.services.linked_panel_service import LinkedPanelService
        LinkedPanelService.start_client_if_linked(app)

        # Hold the outbound ServerKit Cloud relay connection when this
        # panel is paired.
        from app.services import connect_client
        connect_client.start_client_if_paired(app)

