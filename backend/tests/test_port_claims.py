"""Two installs resolving a port at once must not get the same port.

The allocator only looked at app rows, containers and a bind test, none of
which exist yet while an install is still being planned, so concurrent
installs were handed the same port. When the range ran out it returned a
random port that could collide with anything.
"""
import threading

import pytest

from app.exceptions import ConflictError
from app.services import template_ports
from app.services.template_service import TemplateService


@pytest.fixture
def nothing_in_use(monkeypatch):
    monkeypatch.setattr(TemplateService, '_get_database_used_ports', classmethod(lambda cls: set()))
    monkeypatch.setattr(TemplateService, '_get_docker_used_ports', classmethod(lambda cls: set()))
    monkeypatch.setattr(template_ports, '_claimed_ports', {})


def test_concurrent_claims_get_distinct_ports(nothing_in_use):
    got, start = [], threading.Barrier(8)

    def claim():
        start.wait()
        got.append(TemplateService._claim_port(41000))

    threads = [threading.Thread(target=claim) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(got) == 8 and len(set(got)) == 8


def test_claimed_port_is_not_suggested_or_free(nothing_in_use):
    claimed = TemplateService._claim_port(41100)
    assert TemplateService._find_available_port(41100) != claimed
    assert TemplateService._port_is_free(claimed) is False


def test_claims_expire(nothing_in_use, monkeypatch):
    claimed = TemplateService._claim_port(41200)
    monkeypatch.setattr(template_ports, '_PORT_CLAIM_TTL', -1)
    assert TemplateService._find_available_port(41200) == claimed


def test_port_variable_resolution_claims(nothing_in_use):
    first = TemplateService._claim_port(41300)
    assert TemplateService._claim_port(41300) != first


def test_exhausted_range_raises_instead_of_a_random_port(nothing_in_use, monkeypatch):
    monkeypatch.setattr(TemplateService, '_get_database_used_ports',
                        classmethod(lambda cls: set(range(41400, 41410))))
    with pytest.raises(ConflictError, match='No free port'):
        TemplateService._find_available_port(41400, max_attempts=10)
