from celery import Celery
from dotenv import load_dotenv
load_dotenv()
from ..config import redis_settings

app = Celery(
    "fastship_worker",
    broker=redis_settings.REDIS_URL(1),
    backend=redis_settings.REDIS_URL(2),
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

app.autodiscover_tasks(['project1.celery_module.worker'])
