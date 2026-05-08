from fastapi import status
from sqlalchemy import select

from app.accounts.models import User, ActivationToken


DEFAULT_PASSWORD = "Test321!"


async def register_user(
    client,
    email: str,
    password: str = DEFAULT_PASSWORD,
):
    response = await client.post(
        "/register/",
        json={
            "email": email,
            "password": password,
        },
    )

    return response


async def get_activation_token(
    db_session,
    email: str,
) -> ActivationToken:
    result = await db_session.execute(
        select(ActivationToken)
        .join(ActivationToken.user)
        .where(User.email == email)
    )

    activation_token = result.scalar_one_or_none()

    assert activation_token is not None

    return activation_token


async def activate_user(
    client,
    db_session,
    email: str,
):
    activation_token = await get_activation_token(
        db_session=db_session,
        email=email,
    )

    response = await client.post(
        "/activate/",
        json={
            "email": email,
            "token": activation_token.token,
        },
    )

    return response


async def register_and_activate_user(
    client,
    db_session,
    email: str,
    password: str = DEFAULT_PASSWORD,
):
    await register_user(
        client=client,
        email=email,
        password=password,
    )

    await activate_user(
        client=client,
        db_session=db_session,
        email=email,
    )


async def login_user(
    client,
    email: str,
    password: str = DEFAULT_PASSWORD,
):
    response = await client.post(
        "/login/",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == status.HTTP_200_OK

    return response


async def get_auth_headers(
    client,
    email: str,
    password: str = DEFAULT_PASSWORD,
):
    response = await login_user(
        client=client,
        email=email,
        password=password,
    )

    data = response.json()
    access_token = data["access_token"]

    return {
        "Authorization": f"Bearer {access_token}"
    }