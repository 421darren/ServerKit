"""Docker being down is an error, not an empty host.

list_containers returned [] when `docker ps` failed, so the Containers
page said "no containers" on a box running dozens. The local branch of
RemoteDockerService also passed `all=` to a function whose parameter is
`all_containers`, so it always failed with a TypeError.
"""
import pytest

from app.exceptions import DependencyUnavailableError
from app.services.docker_service import DockerService
from app.services.remote_docker_service import RemoteDockerService
from factories import headers_for, make_user

PS_ROW = ('{"ID": "abc", "Names": "web", "Image": "nginx", "Status": "Up", '
          '"State": "running", "Ports": "", "CreatedAt": "now", "Size": "0B"}')


def test_daemon_down_raises_instead_of_listing_nothing(fake_subprocess):
    fake_subprocess.script(['docker', 'ps'], returncode=1,
                           stderr='Cannot connect to the Docker daemon')
    with pytest.raises(DependencyUnavailableError, match='Cannot connect'):
        DockerService.list_containers()


def test_containers_route_answers_503_when_docker_is_down(app, client, fake_subprocess):
    from app import db
    headers = headers_for(make_user(db, 'dk_admin', 'admin'))
    fake_subprocess.script(['docker', 'ps'], returncode=1,
                           stderr='Cannot connect to the Docker daemon')
    resp = client.get('/api/v1/docker/containers', headers=headers)
    assert resp.status_code == 503
    assert 'Docker is not reachable' in resp.get_json()['error']


def test_local_remote_docker_listing_works(fake_subprocess):
    fake_subprocess.script(['docker', 'ps'], stdout=PS_ROW)
    result = RemoteDockerService.list_containers('local', all=True)
    assert result['success'], result
    assert [c['name'] for c in result['data']] == ['web']
