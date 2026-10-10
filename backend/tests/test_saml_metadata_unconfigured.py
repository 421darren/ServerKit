"""SAML metadata on a panel without SAML is a 404, not a recorded crash.

The route is public, so probes against unconfigured panels used to fill
the error log with an "unexpected" OneLogin settings error each time.
"""


def test_unconfigured_saml_metadata_is_404(client):
    resp = client.get('/api/v1/sso/saml/metadata')
    assert resp.status_code == 404
    assert resp.get_json()['code'] == 'sso.saml_not_configured'
