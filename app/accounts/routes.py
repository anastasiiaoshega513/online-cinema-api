from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.models import ActivationToken, User
from accounts.schemas import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    UserActivationRequestSchema
from accounts.services import get_user_by_email, create_user
from db.dependencies import get_db

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
