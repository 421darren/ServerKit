"""Stopping a log stream must end `tail -f` even when the log is quiet.

The stop flag was checked between lines, and readline() blocks until the
log grows, so on a quiet log the stop never fired: every closed log viewer
left a `sudo tail -f` running for the life of the panel.
"""
import sys
import threading
import time

import psutil
import pytest

from app.services import log_service
from app.services.log_service import LogService, LogStreamer


@pytest.fixture
def quiet_log(tmp_path, monkeypatch):
    """A real child that writes one line and then goes quiet, like `tail -f`
    on an idle log. It records its pid so the test can see whether it died."""
    path = tmp_path / 'app.log'
    path.write_text('')
    pid_file = tmp_path / 'tail.pid'
    stand_in = [sys.executable, '-c',
                f'import os, time; open({str(pid_file)!r}, "w").write(str(os.getpid())); '
                f'print("hello", flush=True); time.sleep(600)']
    monkeypatch.setattr(LogService, 'is_path_allowed', classmethod(lambda cls, p: True))
    monkeypatch.setattr(log_service, 'privileged_cmd', lambda cmd: stand_in)
    pids = []

    def tail_pid():
        if not pids:
            pids.append(int(pid_file.read_text()))
        return pids[0]

    yield str(path), tail_pid
    for pid in pids:
        try:
            psutil.Process(pid).kill()
        except psutil.Error:
            pass


def _gone(pid, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
                return True
        except psutil.NoSuchProcess:
            return True
        time.sleep(0.1)
    return False


def test_stop_ends_tail_on_a_quiet_log(quiet_log):
    path, tail_pid = quiet_log
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
    assert _gone(tail_pid())


def test_stopping_a_stream_reaps_its_tail(quiet_log):
    path, tail_pid = quiet_log
    streamer = LogStreamer()
    q = streamer.start_stream('sid-1', path)
    assert q.get(timeout=10)['line'] == 'hello'

    streamer.stop_stream('sid-1')
    assert _gone(tail_pid())
