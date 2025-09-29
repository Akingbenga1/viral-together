#!/usr/bin/env python3
"""
Redis Cleanup Script
Clears all Celery and task-related keys from Redis
"""

import redis
import sys

def cleanup_redis():
    """Clean up all Celery and task-related keys from Redis"""
    try:
        r = redis.from_url('redis://localhost:6379/0')
        print('🧹 Clearing all Celery and Kombu keys...')

        # Get all keys
        all_keys = r.keys('*')
        celery_keys = [k for k in all_keys if b'celery' in k.lower()]
        kombu_keys = [k for k in all_keys if b'kombu' in k.lower()]
        task_keys = [k for k in all_keys if b'task' in k.lower()]

        print(f'Found {len(celery_keys)} Celery keys')
        print(f'Found {len(kombu_keys)} Kombu keys') 
        print(f'Found {len(task_keys)} Task keys')

        # Delete all Celery-related keys
        if celery_keys:
            r.delete(*celery_keys)
            print(f'✅ Deleted {len(celery_keys)} Celery keys')

        if kombu_keys:
            r.delete(*kombu_keys)
            print(f'✅ Deleted {len(kombu_keys)} Kombu keys')

        if task_keys:
            r.delete(*task_keys)
            print(f'✅ Deleted {len(task_keys)} Task keys')

        # Clear all queues
        for queue in ['celery', 'recommendations', 'ai_agents', 'analytics']:
            try:
                r.delete(queue)
                print(f'✅ Cleared queue: {queue}')
            except:
                pass

        print(f'📊 Total keys remaining: {len(r.keys("*"))}')
        print('🎯 Redis cleanup complete!')
        
    except Exception as e:
        print(f'❌ Error cleaning Redis: {e}')
        sys.exit(1)

if __name__ == "__main__":
    cleanup_redis()
