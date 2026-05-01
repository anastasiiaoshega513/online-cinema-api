from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.models import ActivationToken
from accounts.schemas import UserRegistrationResponseSchema, UserRegistrationRequestSchema
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
