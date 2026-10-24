"""Byte-for-byte characterization of the pre-extraction vhost pipeline.

The digest for each app type covers SSL, cache, immutable assets and WordPress
protection together (including rejected combinations), plus TTL boundaries.
Semantic assertions live in the existing nginx/cache/HTTPS suites. These hashes
specifically detect accidental template whitespace or pipeline-order changes.
"""
import hashlib
import itertools
import json
from pathlib import Path

import pytest

from app.services.nginx_service import NginxService


APP_TYPES = ('php', 'wordpress', 'flask', 'django', 'python', 'docker', 'remote', 'static')
SNAPSHOT = Path(__file__).with_name('fixtures') / 'nginx-render-contract.json'


def render_contract(app_type):
    results = []
    for ssl, cache, immutable, wordpress in itertools.product((False, True), repeat=4):
        for ttl in (None, 0, 10, 999):
            results.append(NginxService.render_site_config(
                'shop', app_type, ['shop.example.com', 'www.shop.example.com'],
                root_path='/srv/shop/public', port=8123, upstream='10.0.0.5:8123',
                ssl_cert='/certs/shop.pem' if ssl else None,
                ssl_key='/certs/shop.key' if ssl else None,
                micro_cache=cache, micro_cache_ttl=ttl,
                immutable_assets=immutable, wordpress_protection=wordpress,
            ))
    return hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize('app_type', APP_TYPES)
def test_generated_vhosts_preserve_existing_output(app_type):
    expected = json.loads(SNAPSHOT.read_text())
    assert render_contract(app_type) == expected[app_type]
