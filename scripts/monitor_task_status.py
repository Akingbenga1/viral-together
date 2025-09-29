#!/usr/bin/env python3
"""
Monitor task status changes in real-time
"""

import os
import sys
import asyncio
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def monitor_task_status(task_id: str, max_wait_time: int = 300):
    """
    Monitor a task status until it completes or times out
    """
    try:
        # Use environment variable or default
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/viral_together")
        engine = create_async_engine(database_url, echo=False)
        
        print(f"🔍 Monitoring task: {task_id}")
        print(f"⏰ Max wait time: {max_wait_time} seconds")
        print("=" * 80)
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait_time:
            async with engine.connect() as connection:
                query = text("""
                    SELECT task_id, status, message, created_at, completed_at, 
                           result, error_details, celery_task_id
                    FROM task_status 
                    WHERE task_id = :task_id
                """)
                result = await connection.execute(query, {"task_id": task_id})
                row = result.fetchone()
                
                if row:
                    current_status = row.status
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Only print if status changed
                    if current_status != last_status:
                        print(f"[{current_time}] Status: {current_status}")
                        print(f"  Message: {row.message}")
                        print(f"  Created: {row.created_at}")
                        if row.completed_at:
                            print(f"  Completed: {row.completed_at}")
                        if row.celery_task_id:
                            print(f"  Celery ID: {row.celery_task_id}")
                        print("-" * 40)
                        
                        last_status = current_status
                    
                    # Check if task is completed
                    if current_status in ['completed', 'failed', 'cancelled']:
                        print(f"✅ Task {current_status}!")
                        if row.result:
                            print(f"📄 Result preview: {str(row.result)[:200]}...")
                        if row.error_details:
                            print(f"❌ Error: {row.error_details}")
                        break
                else:
                    print(f"❌ Task {task_id} not found in database")
                    break
            
            # Wait 3 seconds before next check
            await asyncio.sleep(3)
        
        else:
            print(f"⏰ Timeout reached ({max_wait_time}s). Task may still be processing.")
            
    except Exception as e:
        print(f"❌ Error monitoring task: {e}")
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor_task_status.py <task_id>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    asyncio.run(monitor_task_status(task_id))
