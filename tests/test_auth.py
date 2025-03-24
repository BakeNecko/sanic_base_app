
import pytest

from tests.utils import LOGIN_API_URL, ME_API_URL, REFRESH_API_URL, USER_API_URL


@pytest.mark.asyncio
async def anon_request(app):
    url = app.url_for(USER_API_URL)
    _, response = await app.asgi_client.get(url)
    assert response.status == 401


@pytest.mark.asyncio
async def test_login(
    user_normal,
    default_password,
    app,
):
    url = app.url_for(LOGIN_API_URL)
    body = {
        'email': user_normal.email,
        'password': default_password,
    }
    _, response = await app.asgi_client.post(url, json=body)
    assert response.status == 200
    access_token = response.json['access_token']
    refresh_token = response.json['refresh_token']
    headers = {'Authorization': f'Bearer {access_token}'}

    url = app.url_for(ME_API_URL)
    _, response = await app.asgi_client.get(url, headers=headers)
    assert response.status == 200, response.json

    # Refresh token
    url = app.url_for(REFRESH_API_URL)
    body = {'refresh_token': refresh_token}
    _, response = await app.asgi_client.post(url, json=body)
    assert response.status == 200, response.json
    new_access_token = response.json['access_token']

    # Check new access token
    headers = {'Authorization': f'Bearer {new_access_token}'}
    url = app.url_for(ME_API_URL)
    _, response = await app.asgi_client.get(url, headers=headers)
    assert response.status == 200, response.json


@pytest.mark.asyncio
async def test_expired_jwt(
    app,
    get_jwt_access_expired,
):
    headers = {'Authorization': f'Bearer {get_jwt_access_expired}'}

    url = app.url_for(ME_API_URL)
    _, response = await app.asgi_client.get(url, headers=headers)
    assert response.status == 401, response.json
