#!/usr/bin/env python3
"""
Real-time task status monitoring script for database verification
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def monitor_task_status(task_id: str, max_duration: int = 300):
    """
    Monitor task status in real-time from the database
    """
    try:
        # Use environment variable or default connection string
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/viral_together")
        engine = create_async_engine(database_url, echo=False)

        print(f"🔍 Monitoring task: {task_id}")
        print("=" * 60)
        
        start_time = time.time()
        previous_status = None
        
        while time.time() - start_time < max_duration:
            async with engine.connect() as connection:
                query = text("""
                    SELECT task_id, status, message, created_at, completed_at, 
                           celery_task_id, error_details
                    FROM task_status 
                    WHERE task_id = :task_id
                """)
                result = await connection.execute(query, {"task_id": task_id})
                row = result.fetchone()

                if row:
                    current_status = row.status
                    elapsed = int(time.time() - start_time)
                    
                    # Only print if status changed or every 10 seconds
                    if current_status != previous_status or elapsed % 10 == 0:
                        print(f"⏰ [{elapsed:03d}s] Status: {current_status}")
                        print(f"   Message: {row.message}")
                        print(f"   Created: {row.created_at}")
                        print(f"   Celery ID: {row.celery_task_id}")
                        
                        if row.completed_at:
                            print(f"   Completed: {row.completed_at}")
                            duration = (row.completed_at - row.created_at).total_seconds()
                            print(f"   Duration: {duration:.2f} seconds")
                        
                        if row.error_details:
                            print(f"   Error: {row.error_details}")
                        
                        print("-" * 40)
                        previous_status = current_status
                    
                    # Break if task is completed or failed
                    if current_status in ['completed', 'failed']:
                        print(f"✅ Task {current_status}!")
                        break
                else:
                    print(f"❌ Task {task_id} not found in database")
                    break
            
            await asyncio.sleep(2)  # Check every 2 seconds
        
        print("🏁 Monitoring finished")
        
    except Exception as e:
        print(f"❌ Error monitoring task: {e}")
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python monitor_task_db.py <task_id>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    asyncio.run(monitor_task_status(task_id))