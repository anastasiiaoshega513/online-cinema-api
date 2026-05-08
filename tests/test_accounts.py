import pytest
from fastapi import status
from sqlalchemy import select

from app.accounts.models import ActivationToken
from app.accounts.models import User
from helpers import (
    register_user,
    activate_user,
    register_and_activate_user,
    login_user,
    DEFAULT_PASSWORD,
)


@pytest.mark.asyncio
async def test_register_user_success(client, db_session):
    response = await register_user(client, email="test@example.com")
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["email"] == "test@example.com"

    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.email == "test@example.com"
    assert user.is_active is False


@pytest.mark.asyncio
async def test_register_user_with_duplicate_email_returns_409(client):
    first_response = await register_user(client, email="duplicate@example.com")
    second_response = await register_user(client, email="duplicate@example.com")

    assert first_response.status_code == status.HTTP_201_CREATED
    assert second_response.status_code == status.HTTP_409_CONFLICT

    data = second_response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_activate_user_success(client, db_session):
    await register_user(client, email="activate@example.com")
    await activate_user(client, db_session, email="activate@example.com")

    result = await db_session.execute(
        select(User).where(User.email == "activate@example.com")
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.is_active is True

    result = await db_session.execute(
        select(ActivationToken)
        .join(ActivationToken.user)
        .where(User.email == "activate@example.com")
    )
    deleted_activation_token = result.scalar_one_or_none()

    assert deleted_activation_token is None


@pytest.mark.asyncio
async def test_login_user_success(client, db_session):
    email = "login@example.com"
    password = "Test321!"

    await register_and_activate_user(
        client=client,
        db_session=db_session,
        email=email,
        password=password,
    )

    response = await login_user(
        client=client,
        email=email,
        password=password,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_inactive_user_fails(client):
    email = "inactive-login@example.com"

    await register_user(
        client=client,
        email=email,
    )

    response = await client.post(
        "/login/",
        json={
            "email": email,
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
