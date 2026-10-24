"""A restart must not strand queued work.

The broker only ever delivers 'pending' messages, so a message left
'in_flight' by a dead process was never delivered again, and its Job row
read 'running' forever. Boot recovery fails interrupted jobs visibly and
puts every other stranded message back on the queue.
"""
import pytest

from app import db
from app.jobs import registry
from app.jobs.consumer import JobConsumer
from app.jobs.models import Job
from app.jobs.service import GROUP_SLUG, QUEUE_SLUG, JobService
from app.queue_bus.models import QueueMessage
from app.queue_bus.service import QueueBusService


@pytest.fixture(autouse=True)
def clean_bus(app):
    QueueBusService.reset_broker()
    registry.clear()
    yield
    registry.clear()


def _status(message_id):
    return db.session.get(QueueMessage, message_id).status


def test_job_running_at_restart_fails_and_is_not_rerun(app):
    ran = []
    registry.register('test.deploy', lambda job: ran.append(job.id))
    job = JobService.enqueue('test.deploy')
    message = QueueBusService.receive(GROUP_SLUG, QUEUE_SLUG)[0]
    job.status = Job.STATUS_RUNNING  # the old process died mid-handler
    db.session.commit()

    result = JobService.recover_interrupted()

    job = db.session.get(Job, job.id)
    assert result['failed_jobs'] == 1
    assert job.status == Job.STATUS_FAILED
    assert 'restarted' in job.error_message
    assert _status(message['id']) == QueueMessage.STATUS_COMPLETED
    assert QueueBusService.receive(GROUP_SLUG, QUEUE_SLUG) == []
    assert ran == []


def test_message_received_but_not_started_is_redelivered(app):
    ran = []
    registry.register('test.tick', lambda job: ran.append(job.id))
    job = JobService.enqueue('test.tick')
    QueueBusService.receive(GROUP_SLUG, QUEUE_SLUG)  # received, then the process died
    assert QueueBusService.receive(GROUP_SLUG, QUEUE_SLUG) == []

    assert JobService.recover_interrupted()['released_messages'] == 1

    redelivered = QueueBusService.receive(GROUP_SLUG, QUEUE_SLUG)
    assert len(redelivered) == 1
    JobConsumer().process_message(redelivered[0])
    assert ran == [job.id]
    assert db.session.get(Job, job.id).status == Job.STATUS_SUCCEEDED


def test_stranded_message_out_of_attempts_is_dead_lettered(app):
    QueueBusService.ensure_queue('g', 'q')
    sent = QueueBusService.send('g', 'q', {'n': 1}, max_attempts=1)
    QueueBusService.receive('g', 'q')

    QueueBusService.recover_in_flight()

    assert _status(sent['id']) == QueueMessage.STATUS_DEAD_LETTER
    assert QueueBusService.receive('g', 'q') == []
