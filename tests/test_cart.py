import pytest
from fastapi import status

from tests.helpers import (
    create_movie,
    get_auth_headers,
    register_and_activate_user,
)


@pytest.mark.asyncio
async def test_authorized_user_can_get_empty_cart(client, db_session):
    email = "cart-empty@example.com"

    await register_and_activate_user(
        client=client,
        db_session=db_session,
        email=email,
    )

    headers = await get_auth_headers(
        client=client,
        email=email,
    )

    response = await client.get(
        "/cart/",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "detail" in data
    assert "items" not in data or data["items"] == []


@pytest.mark.asyncio
async def test_user_can_add_movie_to_cart(client, db_session):
    email = "cart-add@example.com"

    await register_and_activate_user(
        client=client,
        db_session=db_session,
        email=email,
    )

    headers = await get_auth_headers(
        client=client,
        email=email,
    )

    movie = await create_movie(
        db_session=db_session,
        name="Cart Test Movie",
    )

    response = await client.post(
        f"/cart/items/{movie.id}/",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["movie"]["name"] == "Cart Test Movie"


@pytest.mark.asyncio
async def test_user_cannot_add_same_movie_twice(client, db_session):
    email = "cart-duplicate@example.com"

    await register_and_activate_user(
        client=client,
        db_session=db_session,
        email=email,
    )

    headers = await get_auth_headers(
        client=client,
        email=email,
    )

    movie = await create_movie(
        db_session=db_session,
        name="Duplicate Cart Movie",
    )

    first_response = await client.post(
        f"/cart/items/{movie.id}/",
        headers=headers,
    )

    second_response = await client.post(
        f"/cart/items/{movie.id}/",
        headers=headers,
    )

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_400_BAD_REQUEST

    data = second_response.json()
    assert "already" in data["detail"]
