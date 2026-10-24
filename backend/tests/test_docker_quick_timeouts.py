"""Docker metadata reads are bounded.

ps / inspect / info / version ran with timeout=None, so a wedged dockerd
held every request thread that asked forever. Long operations (pull,
build, compose up, logs) stay unbounded on purpose.
"""
from unittest.mock import patch

import pytest

from app.services.docker_service import QUICK_TIMEOUT, DockerService

OK = {'success': True, 'output': '', 'stderr': '', 'error': None, 'returncode': 0}


@pytest.mark.parametrize('call', [
    lambda: DockerService.list_containers(),
    lambda: DockerService.get_container('abc'),
    lambda: DockerService.get_docker_info(),
    lambda: DockerService.is_docker_installed(),
    lambda: DockerService.tag_image('a:1', 'a:2'),
])
def test_metadata_reads_pass_a_timeout(call):
    with patch.object(DockerService, 'run', return_value=OK) as run:
        call()
    assert run.call_args.kwargs['timeout'] == QUICK_TIMEOUT


def test_quick_timeout_is_bounded():
    assert 0 < QUICK_TIMEOUT <= 60
