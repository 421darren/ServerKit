"""What each source provider's OAuth plumbing sends and stores.

GitHub, GitLab and Bitbucket shared one config/authorize/callback shape,
written out three times. These pin the per-provider differences that the
shared implementation has to keep: how the token request authenticates,
which profile fields become the connection, where granted scopes come
back, and which authorize parameters each provider gets.
"""
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from flask import session

from app.services.settings_service import SettingsService
from app.services.source_connection_service import SourceConnectionService as SC
from factories import make_user

PROFILES = {
    'github': {'id': 7, 'login': 'octo', 'name': 'Octo Cat', 'avatar_url': 'https://a/gh.png'},
    'gitlab': {'id': 8, 'username': 'tanuki', 'name': 'Tanu Ki', 'avatar_url': 'https://a/gl.png'},
    'bitbucket': {'uuid': '{abc-123}', 'username': 'bucky', 'display_name': 'Bu Cky',
                  'links': {'avatar': {'href': 'https://a/bb.png'}}},
}
TOKENS = {
    'github': {'access_token': 'tok-gh', 'scope': 'repo'},
    'gitlab': {'access_token': 'tok-gl', 'scope': 'read_api'},
    'bitbucket': {'access_token': 'tok-bb', 'scopes': ['repository:read', 'account:read']},
}
EXPECTED = {
    'github': ('7', 'octo', 'Octo Cat', 'https://a/gh.png', 'repo'),
    'gitlab': ('8', 'tanuki', 'Tanu Ki', 'https://a/gl.png', 'read_api'),
    'bitbucket': ('abc-123', 'bucky', 'Bu Cky', 'https://a/bb.png', 'repository:read account:read'),
}
TOKEN_URLS = {'github': SC.GITHUB_TOKEN_URL, 'gitlab': SC.GITLAB_TOKEN_URL,
              'bitbucket': SC.BITBUCKET_TOKEN_URL}
PROVIDERS = ['github', 'gitlab', 'bitbucket']


def configure(provider):
    SettingsService.set(f'source_{provider}_client_id', 'cid')
    SettingsService.set(f'source_{provider}_client_secret', 'sec-1234')
    SettingsService.set('source_github_app_slug', '')


@pytest.mark.parametrize('provider', PROVIDERS)
def test_config_reads_redacts_and_keeps_the_secret_on_a_masked_update(app, provider):
    with app.test_request_context():
        configure(provider)
        config = getattr(SC, f'get_{provider}_config')(redacted=True)
        assert (config['client_id'], config['client_secret'], config['configured']) == \
            ('cid', '****1234', True)
        result = getattr(SC, f'update_{provider}_config')(
            {'client_id': 'cid2', 'client_secret': '****1234'})
        assert result['updated'] == ['client_id']
        assert getattr(SC, f'get_{provider}_config')()['client_secret'] == 'sec-1234'


@pytest.mark.parametrize('provider,scope', [
    ('github', 'repo read:user user:email'),
    ('gitlab', 'read_user read_api read_repository'),
    ('bitbucket', None),  # Bitbucket scopes come from the consumer, not the URL
])
def test_authorize_url_parameters(app, provider, scope):
    with app.test_request_context():
        configure(provider)
        url, state = getattr(SC, f'generate_{provider}_authorize_url')('https://p/cb')
        params = {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}
        assert params.get('scope') == scope
        assert params['state'] == state == session[f'source_{provider}_state']
        assert ('response_type' in params) == (provider != 'github')
        assert ('allow_signup' in params) == (provider == 'github')


@pytest.mark.parametrize('provider', PROVIDERS)
def test_callback_exchanges_the_code_and_stores_the_profile(app, provider):
    from app import db
    user = make_user(db, f'sc_{provider}')
    posted = {}

    def fake_post(url, **kwargs):
        posted.update(url=url, **kwargs)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: TOKENS[provider])

    with app.test_request_context():
        configure(provider)
        session[f'source_{provider}_state'] = 'st'
        with patch('app.services.source_connection_service.requests.post', side_effect=fake_post), \
                patch.object(SC, f'_{provider}_get', return_value=PROFILES[provider]):
            conn = getattr(SC, f'complete_{provider}_callback')(user.id, 'the-code', 'st', 'https://p/cb')

    assert posted['url'] == TOKEN_URLS[provider]
    assert posted['data']['code'] == 'the-code'
    assert posted['data']['redirect_uri'] == 'https://p/cb'
    if provider == 'bitbucket':
        assert posted['auth'] == ('cid', 'sec-1234')
        assert 'client_secret' not in posted['data']
    else:
        assert posted['data']['client_secret'] == 'sec-1234'
        assert 'auth' not in posted
    assert ('grant_type' in posted['data']) == (provider != 'github')
    assert (conn.provider, conn.provider_account_id, conn.provider_username, conn.display_name,
            conn.avatar_url, conn.scope) == (provider, *EXPECTED[provider])
    assert conn.access_token == TOKENS[provider]['access_token']


@pytest.mark.parametrize('provider', PROVIDERS)
def test_callback_rejects_a_state_mismatch(app, provider):
    with app.test_request_context():
        configure(provider)
        session[f'source_{provider}_state'] = 'st'
        with pytest.raises(ValueError, match='OAuth state'):
            getattr(SC, f'complete_{provider}_callback')(1, 'c', 'other', 'https://p/cb')


@pytest.mark.parametrize('provider', PROVIDERS)
def test_token_lookup_needs_a_connection(app, provider):
    with pytest.raises(ValueError, match='is not connected'):
        getattr(SC, f'_get_{provider}_token')(424242)
