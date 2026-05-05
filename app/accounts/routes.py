from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.dependencies import get_current_user
from app.accounts.schemas import PasswordResetResponseSchema, ProfileResponseSchema, ProfileRequestSchema
from app.accounts.models import ActivationToken, User, PasswordResetToken, RefreshToken, UserProfile
from app.accounts.schemas import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    UserActivationRequestSchema, PasswordResetRequestSchema, PasswordResetCompleteRequestSchema, \
    UserLoginResponseSchema, UserLoginRequestSchema, TokenRefreshResponseSchema, TokenRefreshRequestSchema
from app.accounts.services import get_user_by_email, create_user
from db.dependencies import get_db
from app.security.tokens import create_access_token, REFRESH_TOKEN_EXPIRE_DAYS, \
    create_refresh_token, decode_refresh_token

router = APIRouter()


@router.post("/register/", response_model=UserRegistrationResponseSchema, status_code=status.HTTP_201_CREATED)
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
        or activation_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
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


@router.post("/password-reset/request/", response_model=PasswordResetResponseSchema)
async def password_reset(
    user: PasswordResetRequestSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.password_reset_token))
        .where(User.email == str(user.email))
    )
    db_user = result.scalar_one_or_none()

    if not db_user or not db_user.is_active:
        return {
            "message": "Password reset token generated.",
            "reset_token": None,
        }

    if db_user.password_reset_token is not None:
        await db.delete(db_user.password_reset_token)
        await db.flush()

    new_token = PasswordResetToken(user_id=db_user.id)
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)

    return {
        "message": "Password reset token generated.",
        "reset_token": new_token.token,
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
        reset_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
        or reset_token.token != user.token
    ):
        await db.delete(reset_token)
        await db.commit()
        raise_invalid_email_or_token()

    try:
        db_user.password = user.new_password
        await db.delete(db_user.password_reset_token)
        await db.commit()
        return {"message": "Password reset successfully."}
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password.",
        )


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
)
async def login(
    user: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    db_user = await get_user_by_email(db, str(user.email))

    if not db_user or not db_user.verify_password(user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    user_access_token = create_access_token(user_id=db_user.id)

    user_refresh_token = create_refresh_token(user_id=db_user.id)

    try:
        refresh_token_record = RefreshToken(
            user_id=db_user.id,
            token=user_refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(refresh_token_record)
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        )

    return {
        "access_token": user_access_token,
        "refresh_token": user_refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh/", response_model=TokenRefreshResponseSchema)
async def refresh_token(
    token: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
):

    decoded_refresh_token = decode_refresh_token(token.refresh_token)

    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.token == token.refresh_token)
    )
    db_refresh_token = result.scalar_one_or_none()

    if not db_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found.",
        )

    if decoded_refresh_token["user_id"] != db_refresh_token.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    db_user = db_refresh_token.user
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_access_token = create_access_token(user_id=db_user.id)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.post("/profile/", response_model=ProfileResponseSchema)
async def create_profile(profile: ProfileRequestSchema, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    if current_user.profile is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a profile.",
        )

    profile_data = profile.model_dump(exclude_unset=True)

    new_profile = UserProfile(
        user_id=current_user.id,
        **profile_data,
    )

    db.add(new_profile)

    try:
        await db.commit()
        await db.refresh(new_profile)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the profile.",
        )

    return new_profile
