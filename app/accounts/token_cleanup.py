from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import ActivationToken, PasswordResetToken, RefreshToken


async def cleanup_expired_tokens(db: AsyncSession) -> dict:

    await db.execute(
        delete(ActivationToken).where(ActivationToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None))
    )

    await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None))
    )

    await db.execute(
        delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None))
    )

    await db.commit()

    return {"detail": "Expired tokens have been deleted."}