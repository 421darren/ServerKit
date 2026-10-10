"""Stopping a log stream must end `tail -f` even when the log is quiet.

The stop flag was checked between lines, and readline() blocks until the
log grows, so on a quiet log the stop never fired: every closed log viewer
left a `sudo tail -f` running for the life of the panel.
"""
import sys
import threading
import time

import pytest

from app.services import log_service
from app.services.log_service import LogService, LogStreamer

# Stands in for `tail -f` on a log that writes one line and then goes quiet.
QUIET_TAIL = [sys.executable, '-c',
              'import time; print("hello", flush=True); time.sleep(600)']


@pytest.fixture
def quiet_log(tmp_path, monkeypatch):
    path = tmp_path / 'app.log'
    path.write_text('')
    monkeypatch.setattr(LogService, 'is_path_allowed', classmethod(lambda cls, p: True))
    spawned = []
    real_popen = log_service.subprocess.Popen

    def recording_popen(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        spawned.append(proc)
        return proc

    monkeypatch.setattr(log_service, 'privileged_cmd', lambda cmd: QUIET_TAIL)
    monkeypatch.setattr(log_service.subprocess, 'Popen', recording_popen)
    yield str(path), spawned
    for proc in spawned:
        if proc.poll() is None:
            proc.kill()


def test_stop_ends_tail_on_a_quiet_log(quiet_log):
    path, spawned = quiet_log
    lines, stop = [], threading.Event()
    worker = threading.Thread(target=LogService.tail_log,
                              args=(path, lines.append, stop), daemon=True)
    worker.start()
    for _ in range(100):
        if lines:
            break
        time.sleep(0.1)
    assert lines == [{'line': 'hello', 'filepath': path}]

    stop.set()
    worker.join(timeout=10)
    assert not worker.is_alive()
    assert spawned[0].poll() is not None


def test_stopping_a_stream_reaps_its_tail(quiet_log):
    path, spawned = quiet_log
    streamer = LogStreamer()
    q = streamer.start_stream('sid-1', path)
    assert q.get(timeout=10)['line'] == 'hello'

    streamer.stop_stream('sid-1')
    for _ in range(100):
        if spawned[0].poll() is not None:
            break
        time.sleep(0.1)
    assert spawned[0].poll() is not None
