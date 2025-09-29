#!/usr/bin/env python3
"""
Celery and Redis Monitoring Script
Monitors Celery workers, tasks, and Redis memory usage in real-time
"""

import os
import sys
import time
import json
import subprocess
import psutil
from datetime import datetime
from typing import Dict, List, Optional
import redis
from celery import Celery

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.core.config import settings

class CeleryRedisMonitor:
    def __init__(self):
        self.redis_client = None
        self.celery_app = None
        self.setup_connections()
        
    def setup_connections(self):
        """Setup Redis and Celery connections"""
        try:
            # Redis connection
            redis_url = settings.REDIS_URL
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()  # Test connection
            print("✅ Redis connection established")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.redis_client = None
            
        try:
            # Celery app connection
            from app.core.celery_app import celery_app
            self.celery_app = celery_app
            print("✅ Celery app connection established")
        except Exception as e:
            print(f"❌ Celery app connection failed: {e}")
            self.celery_app = None
    
    def get_redis_info(self) -> Dict:
        """Get Redis memory and connection info"""
        if not self.redis_client:
            return {"error": "Redis not connected"}
            
        try:
            info = self.redis_client.info()
            return {
                "memory_used": info.get('used_memory_human', 'N/A'),
                "memory_peak": info.get('used_memory_peak_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "db_size": self.redis_client.dbsize(),
                "uptime": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {"error": f"Redis info failed: {e}"}
    
    def get_redis_keys(self) -> Dict:
        """Get Redis keys related to Celery"""
        if not self.redis_client:
            return {"error": "Redis not connected"}
            
        try:
            # Get all keys
            all_keys = self.redis_client.keys('*')
            
            # Categorize keys
            celery_keys = [k.decode() for k in all_keys if b'celery' in k.lower()]
            kombu_keys = [k.decode() for k in all_keys if b'kombu' in k.lower()]
            queue_keys = [k.decode() for k in all_keys if any(q in k.decode().lower() for q in ['recommendations', 'ai_agents', 'analytics'])]
            result_keys = [k.decode() for k in all_keys if b'celery-task-meta' in k.lower()]
            
            return {
                "total_keys": len(all_keys),
                "celery_keys": len(celery_keys),
                "kombu_keys": len(kombu_keys),
                "queue_keys": len(queue_keys),
                "result_keys": len(result_keys),
                "sample_celery_keys": celery_keys[:5],
                "sample_queue_keys": queue_keys[:5]
            }
        except Exception as e:
            return {"error": f"Redis keys failed: {e}"}
    
    def get_queue_lengths(self) -> Dict:
        """Get queue lengths for each Celery queue"""
        if not self.redis_client:
            return {"error": "Redis not connected"}
            
        try:
            queues = ['recommendations', 'ai_agents', 'analytics']
            queue_lengths = {}
            
            for queue in queues:
                try:
                    length = self.redis_client.llen(queue)
                    queue_lengths[queue] = length
                except:
                    queue_lengths[queue] = 0
            
            return queue_lengths
        except Exception as e:
            return {"error": f"Queue lengths failed: {e}"}
    
    def get_celery_workers(self) -> Dict:
        """Get Celery worker information"""
        if not self.celery_app:
            return {"error": "Celery app not connected"}
            
        try:
            inspect = self.celery_app.control.inspect()
            
            # Get active workers
            active = inspect.active()
            if not active:
                return {"error": "No active workers found"}
            
            # Get worker stats
            stats = inspect.stats()
            
            # Get registered tasks
            registered = inspect.registered()
            
            return {
                "active_workers": len(active),
                "worker_names": list(active.keys()),
                "total_tasks": sum(len(tasks) for tasks in active.values()),
                "stats": stats,
                "registered_tasks": registered
            }
        except Exception as e:
            return {"error": f"Celery workers failed: {e}"}
    
    def get_system_info(self) -> Dict:
        """Get system resource information"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available": psutil.virtual_memory().available // (1024**3),  # GB
                "disk_usage": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else "N/A"
            }
        except Exception as e:
            return {"error": f"System info failed: {e}"}
    
    def get_process_info(self) -> Dict:
        """Get information about running processes"""
        try:
            celery_processes = []
            redis_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    if 'celery' in proc.info['name'].lower():
                        celery_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cpu_percent": proc.info['cpu_percent'],
                            "memory_percent": proc.info['memory_percent'],
                            "cmdline": ' '.join(proc.info['cmdline'][:3])  # First 3 args
                        })
                    elif 'redis' in proc.info['name'].lower():
                        redis_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cpu_percent": proc.info['cpu_percent'],
                            "memory_percent": proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "celery_processes": celery_processes,
                "redis_processes": redis_processes,
                "total_celery_processes": len(celery_processes),
                "total_redis_processes": len(redis_processes)
            }
        except Exception as e:
            return {"error": f"Process info failed: {e}"}
    
    def print_header(self):
        """Print monitoring header"""
        print("=" * 80)
        print(f"🔍 CELERY & REDIS MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def print_redis_status(self, redis_info: Dict, redis_keys: Dict, queue_lengths: Dict):
        """Print Redis status information"""
        print("\n📊 REDIS STATUS")
        print("-" * 40)
        
        if "error" in redis_info:
            print(f"❌ Redis Error: {redis_info['error']}")
            return
        
        print(f"💾 Memory Used: {redis_info.get('memory_used', 'N/A')}")
        print(f"📈 Memory Peak: {redis_info.get('memory_peak', 'N/A')}")
        print(f"🔗 Connected Clients: {redis_info.get('connected_clients', 0)}")
        print(f"📊 Total Keys: {redis_keys.get('total_keys', 0)}")
        print(f"⏱️  Uptime: {redis_info.get('uptime', 0)} seconds")
        
        print(f"\n📋 QUEUE STATUS")
        print("-" * 20)
        for queue, length in queue_lengths.items():
            if isinstance(length, int):
                status = "🟢" if length == 0 else "🟡" if length < 10 else "🔴"
                print(f"{status} {queue}: {length} tasks")
            else:
                print(f"❌ {queue}: {length}")
        
        print(f"\n🔑 KEY BREAKDOWN")
        print("-" * 20)
        print(f"Celery Keys: {redis_keys.get('celery_keys', 0)}")
        print(f"Kombu Keys: {redis_keys.get('kombu_keys', 0)}")
        print(f"Queue Keys: {redis_keys.get('queue_keys', 0)}")
        print(f"Result Keys: {redis_keys.get('result_keys', 0)}")
    
    def print_celery_status(self, celery_info: Dict):
        """Print Celery status information"""
        print("\n⚙️  CELERY STATUS")
        print("-" * 40)
        
        if "error" in celery_info:
            print(f"❌ Celery Error: {celery_info['error']}")
            return
        
        print(f"👥 Active Workers: {celery_info.get('active_workers', 0)}")
        print(f"📋 Total Tasks: {celery_info.get('total_tasks', 0)}")
        
        if celery_info.get('worker_names'):
            print(f"🖥️  Worker Names: {', '.join(celery_info['worker_names'])}")
        
        if celery_info.get('registered_tasks'):
            total_tasks = sum(len(tasks) for tasks in celery_info['registered_tasks'].values())
            print(f"📝 Registered Tasks: {total_tasks}")
    
    def print_system_status(self, system_info: Dict, process_info: Dict):
        """Print system status information"""
        print("\n💻 SYSTEM STATUS")
        print("-" * 40)
        
        if "error" not in system_info:
            print(f"🖥️  CPU Usage: {system_info.get('cpu_percent', 0):.1f}%")
            print(f"💾 Memory Usage: {system_info.get('memory_percent', 0):.1f}%")
            print(f"💽 Available Memory: {system_info.get('memory_available', 0)} GB")
            print(f"💿 Disk Usage: {system_info.get('disk_usage', 0):.1f}%")
        
        if "error" not in process_info:
            print(f"\n🔄 PROCESSES")
            print("-" * 20)
            print(f"Celery Processes: {process_info.get('total_celery_processes', 0)}")
            print(f"Redis Processes: {process_info.get('total_redis_processes', 0)}")
            
            if process_info.get('celery_processes'):
                print("\n📋 CELERY PROCESSES:")
                for proc in process_info['celery_processes']:
                    print(f"  PID {proc['pid']}: {proc['name']} (CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_percent']:.1f}%)")
    
    def monitor_loop(self, interval: int = 5, max_iterations: int = None):
        """Run monitoring loop"""
        iteration = 0
        
        try:
            while True:
                if max_iterations and iteration >= max_iterations:
                    break
                
                self.print_header()
                
                # Get all monitoring data
                redis_info = self.get_redis_info()
                redis_keys = self.get_redis_keys()
                queue_lengths = self.get_queue_lengths()
                celery_info = self.get_celery_workers()
                system_info = self.get_system_info()
                process_info = self.get_process_info()
                
                # Print status
                self.print_redis_status(redis_info, redis_keys, queue_lengths)
                self.print_celery_status(celery_info)
                self.print_system_status(system_info, process_info)
                
                print(f"\n⏰ Next update in {interval} seconds... (Press Ctrl+C to stop)")
                print("=" * 80)
                
                time.sleep(interval)
                iteration += 1
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
    
    def run_single_check(self):
        """Run a single monitoring check"""
        self.print_header()
        
        redis_info = self.get_redis_info()
        redis_keys = self.get_redis_keys()
        queue_lengths = self.get_queue_lengths()
        celery_info = self.get_celery_workers()
        system_info = self.get_system_info()
        process_info = self.get_process_info()
        
        self.print_redis_status(redis_info, redis_keys, queue_lengths)
        self.print_celery_status(celery_info)
        self.print_system_status(system_info, process_info)
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Celery and Redis')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Monitoring interval in seconds (default: 5)')
    parser.add_argument('--iterations', '-n', type=int, help='Number of iterations (default: infinite)')
    parser.add_argument('--once', '-o', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    monitor = CeleryRedisMonitor()
    
    if args.once:
        monitor.run_single_check()
    else:
        monitor.monitor_loop(interval=args.interval, max_iterations=args.iterations)

if __name__ == "__main__":
    main()
