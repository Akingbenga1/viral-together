#!/usr/bin/env python3
"""
Quick Celery & Redis Monitor
Simple script for quick status checks
"""

import os
import sys
import time
import redis
import subprocess
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_redis():
    """Check Redis status"""
    try:
        r = redis.from_url("redis://localhost:6379/0")
        r.ping()
        
        info = r.info()
        keys = r.keys('*')
        
        print("🔴 REDIS STATUS")
        print(f"  ✅ Connected: Yes")
        print(f"  💾 Memory: {info.get('used_memory_human', 'N/A')}")
        print(f"  📊 Total Keys: {len(keys)}")
        print(f"  🔗 Clients: {info.get('connected_clients', 0)}")
        
        # Check Celery-specific keys
        celery_keys = [k.decode() for k in keys if b'celery' in k.lower()]
        kombu_keys = [k.decode() for k in keys if b'kombu' in k.lower()]
        
        print(f"  🔑 Celery Keys: {len(celery_keys)}")
        print(f"  🔑 Kombu Keys: {len(kombu_keys)}")
        
        # Check queue lengths
        queues = ['recommendations', 'ai_agents', 'analytics']
        print(f"  📋 Queue Status:")
        for queue in queues:
            try:
                length = r.llen(queue)
                status = "🟢" if length == 0 else "🟡" if length < 5 else "🔴"
                print(f"    {status} {queue}: {length}")
            except:
                print(f"    ❌ {queue}: Error")
        
        return True
    except Exception as e:
        print(f"🔴 REDIS STATUS")
        print(f"  ❌ Error: {e}")
        return False

def check_celery():
    """Check Celery status"""
    try:
        # Check if Celery processes are running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        celery_processes = [line for line in result.stdout.split('\n') if 'celery' in line.lower()]
        
        print("⚙️  CELERY STATUS")
        if celery_processes:
            print(f"  ✅ Workers Running: {len(celery_processes)}")
            for proc in celery_processes[:3]:  # Show first 3
                parts = proc.split()
                if len(parts) > 10:
                    print(f"    PID {parts[1]}: {parts[10][:50]}...")
        else:
            print("  ❌ No Celery workers found")
            return False
        
        # Try to get Celery info
        try:
            from app.core.celery_app import celery_app
            inspect = celery_app.control.inspect()
            active = inspect.active()
            
            if active:
                total_tasks = sum(len(tasks) for tasks in active.values())
                print(f"  📋 Active Tasks: {total_tasks}")
                print(f"  👥 Workers: {list(active.keys())}")
            else:
                print("  ⚠️  No active workers found")
        except Exception as e:
            print(f"  ⚠️  Celery info error: {e}")
        
        return True
    except Exception as e:
        print(f"⚙️  CELERY STATUS")
        print(f"  ❌ Error: {e}")
        return False

def check_system():
    """Check system resources"""
    try:
        import psutil
        
        print("💻 SYSTEM STATUS")
        print(f"  🖥️  CPU: {psutil.cpu_percent(interval=1):.1f}%")
        print(f"  💾 Memory: {psutil.virtual_memory().percent:.1f}%")
        print(f"  💽 Available: {psutil.virtual_memory().available // (1024**3)} GB")
        
        return True
    except Exception as e:
        print(f"💻 SYSTEM STATUS")
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Main monitoring function"""
    print("=" * 60)
    print(f"🔍 QUICK CELERY & REDIS MONITOR - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    redis_ok = check_redis()
    celery_ok = check_celery()
    system_ok = check_system()
    
    print("\n" + "=" * 60)
    if redis_ok and celery_ok:
        print("✅ STATUS: All systems operational")
    else:
        print("❌ STATUS: Issues detected")
    print("=" * 60)

if __name__ == "__main__":
    main()
