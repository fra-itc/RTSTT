"""
Celery Application Configuration
Configures Celery with Redis broker for batch audio processing.
"""

import os
import logging
from celery import Celery
from kombu import Exchange, Queue

# Configure logging
logger = logging.getLogger(__name__)

# Get Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Construct Redis URL
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

logger.info(f"Configuring Celery with Redis broker: {REDIS_URL}")

# Create Celery application
celery_app = Celery(
    "rtstt_batch_processor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.core.batch_processor.audio_processor"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600 * 24,  # Results expire after 24 hours
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=True,

    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit

    # Concurrency settings
    worker_concurrency=4,  # 4 parallel workers

    # Routing
    task_default_queue="audio_processing",
    task_default_exchange="audio_processing",
    task_default_routing_key="audio.process",

    # Queue configuration
    task_queues=(
        Queue(
            "audio_processing",
            Exchange("audio_processing"),
            routing_key="audio.process",
            queue_arguments={"x-max-priority": 10}
        ),
    ),

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes
    task_retry_jitter=True,
)

logger.info("Celery application configured successfully")

# Export
__all__ = ["celery_app"]
