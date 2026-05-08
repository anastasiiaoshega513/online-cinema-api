import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import ActivationToken, PasswordResetToken, RefreshToken
from app.accounts.celery_app import celery_app
from db.engine import AsyncSessionLocal


async def cleanup_expired_tokens(db: AsyncSession) -> dict:

    await db.execute(
        delete(ActivationToken).where(
            ActivationToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
        )
    )

    await db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.expires_at
            < datetime.now(timezone.utc).replace(tzinfo=None)
        )
    )

    await db.execute(
        delete(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
        )
    )

    await db.commit()

    return {"detail": "Expired tokens have been deleted."}


async def _cleanup_expired_tokens_runner():
    async with AsyncSessionLocal() as db:
        return await cleanup_expired_tokens(db)


@celery_app.task(name="app.accounts.token_cleanup.cleanup_expired_tokens_task")
def cleanup_expired_tokens_task():
    return asyncio.run(_cleanup_expired_tokens_runner())
