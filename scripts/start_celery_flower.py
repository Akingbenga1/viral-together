#!/usr/bin/env python3
"""
Celery Flower monitoring startup script
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_celery_flower():
    """Start Celery Flower monitoring interface"""
    
    # Set environment variables
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.core.config')
    
    # Flower command
    cmd = [
        'celery',
        '-A', 'app.core.celery_app',
        'flower',
        '--port=5555',
        '--broker=redis://localhost:6379/0'
    ]
    
    print("Starting Celery Flower monitoring...")
    print(f"Command: {' '.join(cmd)}")
    print("Flower will be available at: http://localhost:5555")
    
    try:
        # Start Flower
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down Celery Flower...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery Flower: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_flower()
