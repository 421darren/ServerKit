"""
Regression test: "new IP" alerts must survive a backend restart.

check_new_ip() kept the known addresses only in memory, so every restart of
the panel raised a fresh "First connection from this IP address" alert for
each agent's own, long-known address (h105/h106 each piled up 30+ of them).
"""
from app import db as _db
from app.models.server import Server
from app.models.security_alert import SecurityAlert
from app.services.anomaly_detection_service import anomaly_detection_service as ad


def _new_ip_alerts(server_id, ip):
    return SecurityAlert.query.filter_by(
        alert_type='new_ip', server_id=server_id, source_ip=ip).count()


def test_known_ip_not_realerted_after_restart(app):
    s = Server(name="restart-test", agent_id="agent-newip-restart")
    _db.session.add(s)
    _db.session.commit()
    ip = "203.0.113.10"

    assert ad.check_new_ip(s.id, ip) is True
    assert _new_ip_alerts(s.id, ip) == 1

    # The first alert gets resolved, then the backend restarts (memory empty).
    alert = SecurityAlert.query.filter_by(server_id=s.id, source_ip=ip).first()
    alert.status = 'resolved'
    _db.session.commit()
    ad._known_ips.pop(s.id, None)

    assert ad.check_new_ip(s.id, ip) is False
    assert _new_ip_alerts(s.id, ip) == 1


def test_genuinely_new_ip_still_alerts(app):
    s = Server(name="restart-test-2", agent_id="agent-newip-fresh")
    _db.session.add(s)
    _db.session.commit()

    assert ad.check_new_ip(s.id, "203.0.113.20") is True
    ad._known_ips.pop(s.id, None)
    assert ad.check_new_ip(s.id, "198.51.100.7") is True
    assert _new_ip_alerts(s.id, "198.51.100.7") == 1
