import pytest
from fastapi import status

from app.orders.models import OrderStatusEnum
from tests.helpers import (
    create_movie,
    get_auth_headers,
    register_and_activate_user,
)


@pytest.mark.asyncio
async def test_cannot_create_order_from_empty_cart(client, db_session):
    email = "empty-order@example.com"

    await register_and_activate_user(
        client=client,
        db_session=db_session,
        email=email,
    )

    headers = await get_auth_headers(
        client=client,
        email=email,
    )

    response = await client.post(
        "/orders/",
        headers=headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert "cart" in data["detail"].lower()


@pytest.mark.asyncio
async def test_user_can_create_order_from_cart(client, db_session):
    email = "create-order@example.com"

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
        name="Order Test Movie",
    )

    add_to_cart_response = await client.post(
        f"/cart/items/{movie.id}/",
        headers=headers,
    )

    assert add_to_cart_response.status_code == status.HTTP_200_OK

    order_response = await client.post(
        "/orders/",
        headers=headers,
    )

    assert order_response.status_code in (
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    )

    data = order_response.json()

    assert data["id"] is not None
    assert data["status"] == OrderStatusEnum.PENDING.value
    assert len(data["items"]) == 1
    assert data["items"][0]["movie"]["name"] == "Order Test Movie"
    assert data["items"][0]["price_at_order"] is not None


@pytest.mark.asyncio
async def test_cart_is_cleared_after_order_creation(client, db_session):
    email = "clear-cart-after-order@example.com"

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
        name="Clear Cart Movie",
    )

    add_to_cart_response = await client.post(
        f"/cart/items/{movie.id}/",
        headers=headers,
    )

    assert add_to_cart_response.status_code == status.HTTP_200_OK

    order_response = await client.post(
        "/orders/",
        headers=headers,
    )

    assert order_response.status_code in (
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    )

    cart_response = await client.get(
        "/cart/",
        headers=headers,
    )

    assert cart_response.status_code == status.HTTP_200_OK

    data = cart_response.json()

    assert data.get("items") in (None, [])


@pytest.mark.asyncio
async def test_pending_order_can_be_canceled(client, db_session):
    email = "cancel-order@example.com"

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
        name="Cancel Order Movie",
    )

    add_to_cart_response = await client.post(
        f"/cart/items/{movie.id}/",
        headers=headers,
    )

    assert add_to_cart_response.status_code == status.HTTP_200_OK

    order_response = await client.post(
        "/orders/",
        headers=headers,
    )

    assert order_response.status_code in (
        status.HTTP_200_OK,
        status.HTTP_201_CREATED,
    )

    order_id = order_response.json()["id"]

    cancel_response = await client.patch(
        f"/orders/{order_id}/cancel/",
        headers=headers,
    )

    assert cancel_response.status_code == status.HTTP_200_OK

    data = cancel_response.json()

    assert data["id"] == order_id
    assert data["status"] == OrderStatusEnum.CANCELED.value
