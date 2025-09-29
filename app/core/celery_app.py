"""
Celery application configuration for distributed task processing
"""

import os
from celery import Celery
from app.core.config import settings

# Create Celery instance with minimal configuration
celery_app = Celery("viral_together")

# Configure broker and backend
celery_app.conf.broker_url = settings.REDIS_URL
celery_app.conf.result_backend = settings.REDIS_URL

# Basic configuration - optimized for stability
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    result_expires=3600,
    # Use default queue for simplicity
    task_default_queue='celery',
    task_create_missing_queues=True,
    # Stable configuration
    task_always_eager=False,
    task_eager_propagates=False,
    worker_disable_rate_limits=True,
    # Disable problematic features
    worker_send_task_events=False,
    task_send_sent_event=False,
    # Add worker pool configuration for stability
    worker_pool='threads',  # Use threads instead of processes
    worker_concurrency=2,   # Reduce concurrency
    worker_max_tasks_per_child=1000,  # Restart workers periodically
)

# Health check endpoint
@celery_app.task(bind=True)
def health_check(self):
    """Health check task for monitoring"""
    try:
        return {
            "status": "healthy",
            "worker_id": getattr(self.request, 'id', 'unknown'),
            "timestamp": str(getattr(self.request, 'eta', 'unknown'))
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Simple test task
@celery_app.task
def simple_test_task(message: str):
    """Simple test task to verify Celery is working"""
    return f"Test task received: {message}"

# Alternative task execution without Celery
def execute_task_sync(task_name: str, *args, **kwargs):
    """Execute task synchronously without Celery"""
    if task_name == "process_ai_agent_execution":
        from app.tasks.ai_agent_tasks import process_ai_agent_execution_task
        return process_ai_agent_execution_task(*args, **kwargs)
    elif task_name == "simple_test_task":
        return simple_test_task(*args, **kwargs)
    else:
        raise ValueError(f"Unknown task: {task_name}")

# Import tasks to ensure they are registered
try:
    from app.tasks import recommendation_tasks, ai_agent_tasks, analytics_tasks
except ImportError as e:
    print(f"Warning: Could not import tasks: {e}")
