#!/usr/bin/env python3
"""
Custom Celery Worker Script
Bypasses entry points issues by directly importing and running Celery
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_custom_celery_worker():
    """Start Celery worker directly without entry points"""
    
    # Set environment variables
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.core.config')
    
    try:
        # Import Celery app directly
        from app.core.celery_app import celery_app
        
        print("Starting custom Celery worker...")
        print("Using thread pool for stability")
        
        # Start worker using app.worker_main
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--pool=threads',
            '--concurrency=2',
            '--queues=celery',
            '--hostname=worker@%h',
            '--prefetch-multiplier=1',
            '--max-tasks-per-child=1000'
        ])
        
    except KeyboardInterrupt:
        print("\nShutting down custom Celery worker...")
    except Exception as e:
        print(f"Error starting custom Celery worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_custom_celery_worker()
