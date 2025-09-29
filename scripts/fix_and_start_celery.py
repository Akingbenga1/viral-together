#!/usr/bin/env python3
"""
Fix and Start Celery Workers
This script helps fix the stuck tasks and start Celery workers properly
"""

import os
import sys
import subprocess
import time
import redis
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_redis():
    """Check if Redis is running"""
    try:
        r = redis.from_url("redis://localhost:6379/0")
        r.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        return False

def clear_celery_queues():
    """Clear all Celery queues"""
    try:
        print("🧹 Clearing Celery queues...")
        result = subprocess.run([
            'celery', '-A', 'app.core.celery_app', 'purge', '-f'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Celery queues cleared")
        else:
            print(f"⚠️  Queue clear result: {result.stderr}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to clear queues: {e}")
        return False

def stop_celery_workers():
    """Stop all Celery workers"""
    try:
        print("🛑 Stopping existing Celery workers...")
        
        # Try to stop gracefully
        result = subprocess.run([
            'celery', '-A', 'app.core.celery_app', 'control', 'shutdown'
        ], capture_output=True, text=True, cwd=project_root)
        
        # Force kill any remaining processes
        try:
            subprocess.run(['pkill', '-f', 'celery'], capture_output=True)
        except:
            pass
        
        print("✅ Celery workers stopped")
        return True
    except Exception as e:
        print(f"⚠️  Error stopping workers: {e}")
        return True

def start_celery_worker():
    """Start Celery worker"""
    try:
        print("🚀 Starting Celery worker...")
        
        # Start custom worker in background with virtual environment
        process = subprocess.Popen([
            'python', 'scripts/custom_celery_worker.py'
        ], cwd=project_root)
        
        print(f"✅ Celery worker started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return None

def check_celery_status():
    """Check if Celery is working"""
    try:
        print("🔍 Checking Celery status...")
        
        result = subprocess.run([
            'celery', '-A', 'app.core.celery_app', 'inspect', 'ping'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Celery workers are responding")
            return True
        else:
            print(f"❌ Celery workers not responding: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to check Celery status: {e}")
        return False

def check_redis_keys():
    """Check Redis keys"""
    try:
        r = redis.from_url("redis://localhost:6379/0")
        keys = r.keys('*')
        
        print(f"📊 Redis has {len(keys)} keys")
        
        # Check Celery-specific keys
        celery_keys = [k.decode() for k in keys if b'celery' in k.lower()]
        kombu_keys = [k.decode() for k in keys if b'kombu' in k.lower()]
        
        print(f"🔑 Celery keys: {len(celery_keys)}")
        print(f"🔑 Kombu keys: {len(kombu_keys)}")
        
        # Check queue lengths
        queues = ['recommendations', 'ai_agents', 'analytics']
        for queue in queues:
            try:
                length = r.llen(queue)
                print(f"📋 {queue}: {length} tasks")
            except:
                print(f"❌ {queue}: Error checking length")
        
        return True
    except Exception as e:
        print(f"❌ Failed to check Redis keys: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print(f"🔧 CELERY FIX & START SCRIPT - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Check Redis
    if not check_redis():
        print("❌ Please start Redis first: docker run -d --name redis -p 6379:6379 redis:latest")
        return
    
    # Step 2: Stop existing workers
    stop_celery_workers()
    time.sleep(2)
    
    # Step 3: Clear queues
    clear_celery_queues()
    time.sleep(1)
    
    # Step 4: Check Redis keys
    check_redis_keys()
    
    # Step 5: Start new worker
    worker_process = start_celery_worker()
    if not worker_process:
        print("❌ Failed to start Celery worker")
        return
    
    # Step 6: Wait and check status
    print("⏳ Waiting for worker to start...")
    time.sleep(5)
    
    if check_celery_status():
        print("\n✅ SUCCESS: Celery is now running properly!")
        print("📋 You can now test your endpoints")
        print("🔍 Use the monitoring scripts to watch the system:")
        print("   python scripts/quick_monitor.py")
        print("   python scripts/monitor_celery_redis.py --interval 5")
    else:
        print("\n❌ FAILED: Celery is not responding")
        print("🔍 Check the logs for errors")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
