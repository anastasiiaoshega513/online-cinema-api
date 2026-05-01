from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.models import UserGroup, UserGroupEnum, User
from accounts.schemas import UserRegistrationRequestSchema
from security.passwords import hash_password


async def create_user(db: AsyncSession, user: UserRegistrationRequestSchema):
    hashed = hash_password(user.password)
    result = await db.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    )
    default_group = result.scalar_one_or_none()
    db_user = User(
        email=str(user.email), _hashed_password=hashed, group_id=default_group.id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
