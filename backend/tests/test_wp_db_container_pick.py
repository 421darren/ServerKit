"""
The WordPress backup dumps the database with `docker exec <db container>`.
The DB container was chosen by "mysql" appearing anywhere in the image name,
so kpanel's own site picked its WordPress container
(image serverkit-wordpress:6.4-php8.3-mysqlclient) instead of kpanel-db, and
every nightly backup since 12 Oct failed with "Can't connect to local server
through socket '/run/mysqld/mysqld.sock'".
"""
import importlib.util
import pathlib

import pytest

_PATH = (pathlib.Path(__file__).resolve().parents[1]
         / 'app' / 'plugins' / 'serverkit-wordpress' / 'wordpress_service.py')


@pytest.fixture(scope='module')
def WPS():
    spec = importlib.util.spec_from_file_location('wp_service_under_test', _PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.WordPressService


KPANEL_COMPOSE = """
services:
  wordpress:
    image: serverkit-wordpress:6.4-php8.3-mysqlclient
    container_name: kpanel
  redis:
    image: redis:7-alpine
    container_name: kpanel-redis
  db:
    image: mysql:8.0
    container_name: kpanel-db
"""


def _site(tmp_path, compose):
    (tmp_path / 'docker-compose.yml').write_text(compose)
    return str(tmp_path)


def test_kpanel_layout_picks_the_real_db(WPS, tmp_path):
    assert WPS._docker_db_container(_site(tmp_path, KPANEL_COMPOSE)) == 'kpanel-db'


@pytest.mark.parametrize('image,expected', [
    ('mysql:8.0', True),
    ('mariadb:11', True),
    ('docker.io/library/mariadb:10.11', True),
    ('registry.local:5000/percona/percona-server:8.0', True),
    ('mysql@sha256:abc', True),
    ('serverkit-wordpress:6.4-php8.3-mysqlclient', False),
    ('wordpress:php8.3-fpm', False),
    ('phpmyadmin/phpmyadmin', False),
    ('redis:7-alpine', False),
])
def test_is_db_image(WPS, image, expected):
    assert WPS._is_db_image(image) is expected


def test_falls_back_to_service_named_db(WPS, tmp_path):
    compose = """
services:
  wordpress:
    image: wordpress:latest
    container_name: site-wp
  db:
    image: my-registry/custom-sql:1
    container_name: site-db
"""
    assert WPS._docker_db_container(_site(tmp_path, compose)) == 'site-db'


def test_mariadb_first_in_file_still_works(WPS, tmp_path):
    compose = """
services:
  database:
    image: mariadb:11
    container_name: a-db
  wordpress:
    image: wordpress:latest
"""
    assert WPS._docker_db_container(_site(tmp_path, compose)) == 'a-db'
