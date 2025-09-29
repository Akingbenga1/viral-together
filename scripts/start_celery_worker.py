#!/usr/bin/env python3
"""
Celery worker startup script for distributed task processing
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_celery_worker():
    """Start Celery worker with proper configuration"""
    
    # Set environment variables
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.core.config')
    
    # Use Python module approach to avoid entry points issues
    cmd = [
        'python', '-m', 'celery',
        '-A', 'app.core.celery_app',
        'worker',
        '--loglevel=info',
        '--pool=threads',  # Use threads instead of processes
        '--concurrency=2',  # Reduced concurrency
        '--queues=celery',  # Use default queue
        '--hostname=worker@%h',
        '--prefetch-multiplier=1',
        '--max-tasks-per-child=1000'  # Restart workers less frequently
    ]
    
    print("Starting Celery worker...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Start the worker
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down Celery worker...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_worker()
