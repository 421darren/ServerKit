"""PUT /apps/<id>/env/<key> partial-update semantics at the route boundary.

The service door (EnvService.update_env_var) distinguishes "field absent"
(_UNSET, leave untouched) from "field explicitly null" (clear it). The route
must preserve that distinction for description: a JSON null clears, an omitted
key leaves the stored text alone.
"""
from app import db
from app.models import Application


def _seed_var(app):
    from app.services.env_service import EnvService
    from factories import make_application, make_user

    user = make_user(db, role='admin')
    application = make_application(db, name='env-api-app', user_id=user.id)
    EnvService.set_env_var(
        application.id, 'API_URL', 'https://api.example.test',
        description='where the API lives', user_id=user.id,
    )
    return application, user


def test_null_description_clears_but_omitted_leaves_it(app, client):
    from factories import headers_for

    with app.app_context():
        application, user = _seed_var(app)
        headers = headers_for(user)
        app_id = application.id

    # Omitting description entirely must not touch it.
    res = client.put(f'/api/v1/apps/{app_id}/env/API_URL',
                     json={'value': 'https://api2.example.test'},
                     headers=headers)
    assert res.status_code == 200
    assert res.get_json()['env_var']['description'] == 'where the API lives'

    # An explicit JSON null clears it.
    res = client.put(f'/api/v1/apps/{app_id}/env/API_URL',
                     json={'description': None},
                     headers=headers)
    assert res.status_code == 200
    assert res.get_json()['env_var']['description'] is None


def test_effective_view_is_value_free_and_app_scoped(app, client):
    from factories import headers_for, make_user
    with app.app_context():
        application, owner = _seed_var(app)
        app_id = application.id
        owner_headers = headers_for(owner)
        stranger = make_user(db, role='viewer')
        stranger_headers = headers_for(stranger)
    url = f'/api/v1/apps/{app_id}/env?view=effective'
    response = client.get(url, headers=owner_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['values_hidden'] and data['complete']
    assert data['env_vars'][0]['key'] == 'API_URL'
    assert 'https://api.example.test' not in response.get_data(as_text=True)
    assert 'value' not in data['env_vars'][0]
    assert client.get(url, headers=stranger_headers).status_code in (403, 404)
    assert client.get(url).status_code == 401
    assert client.get(url + '&service=bad/name', headers=owner_headers).status_code == 400
