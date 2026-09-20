"""
MAARS Lens: Celery Application Entry Point
==========================================
Defines the Celery application configured with Redis broker and result backend.
Used for running background PaddleOCR extraction, polygon annotation rendering,
and multi-panel fact merging.
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "maars_lens_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 minutes hard limit
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
)
