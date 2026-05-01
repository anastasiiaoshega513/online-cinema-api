from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.models import ActivationToken, User, PasswordResetToken
from accounts.schemas import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    UserActivationRequestSchema, PasswordResetRequestSchema, PasswordResetCompleteRequestSchema
from accounts.services import get_user_by_email, create_user
from db.dependencies import get_db
from security.passwords import hash_password

router = APIRouter()


@router.post("register", response_model=UserRegistrationResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, str(user.email))
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with this email {user.email} already exists.",
        )

    try:
        new_user = await create_user(db, user)
        activation_token = ActivationToken(user_id=new_user.id)
        db.add(activation_token)
        await db.commit()

        return new_user
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        )


@router.post("/activate/", response_model=MessageResponseSchema)
async def activate(
    user: UserActivationRequestSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.activation_token))
        .where(User.email == str(user.email))
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email."
        )

    activation_token = db_user.activation_token
    if (
        not activation_token
        or activation_token.token != user.token
        or activation_token.expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation token.",
        )

    if db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is already active.",
        )

    db_user.is_active = True
    await db.delete(activation_token)
    await db.commit()
    return {"message": "User account activated successfully."}


@router.post("/password-reset/request/", response_model=MessageResponseSchema)
async def password_reset(
    user: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.password_reset_token))
        .where(User.email == str(user.email))
    )
    db_user = result.scalar_one_or_none()

    if db_user and db_user.is_active:
        if db_user.password_reset_token is not None:
            await db.delete(db_user.password_reset_token)
            await db.flush()

        new_token = PasswordResetToken(user_id=db_user.id)
        db.add(new_token)
        await db.commit()

    return {
        "message": "If you are registered, you will receive an email with instructions."
    }


def raise_invalid_email_or_token() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token."
    )


@router.post("/reset-password/complete/", response_model=MessageResponseSchema)
async def reset_password(
    user: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.password_reset_token))
        .where(User.email == str(user.email))
    )
    db_user = result.scalar_one_or_none()

    if not db_user or not db_user.is_active or not db_user.password_reset_token:
        raise_invalid_email_or_token()

    reset_token = db_user.password_reset_token

    if (
        reset_token.expires_at < datetime.now(timezone.utc)
        or reset_token.token != user.token
    ):
        await db.delete(reset_token)
        await db.commit()
        raise_invalid_email_or_token()

    try:
        db_user.password = hash_password(user.new_password)
        await db.delete(db_user.password_reset_token)
        await db.commit()
        return {"message": "Password reset successfully."}
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password.",
        )
