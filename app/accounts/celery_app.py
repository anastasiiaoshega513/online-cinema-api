import os

from celery import Celery

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0",
)

CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/1",
)

celery_app = Celery(
    "online_cinema",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.accounts.token_cleanup",
    ],
)

celery_app.conf.update(
    timezone="UTC",
    beat_schedule={
        "cleanup-expired-tokens-every-hour": {
            "task": "app.accounts.token_cleanup.cleanup_expired_tokens_task",
            "schedule": 60 * 60,
        },
    },
)
