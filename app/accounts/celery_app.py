from celery import Celery

celery_app = Celery(
    "online_cinema",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
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
