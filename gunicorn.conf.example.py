# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"  # Only listen on localhost (Nginx will handle external traffic)
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/root/projects/viral-together/logs/access.log"
errorlog = "/root/projects/viral-together/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "viral-together"

# Server mechanics
daemon = False
pidfile = "/root/projects/viral-together/gunicorn.pid"
user = "root"
group = "root"
tmp_upload_dir = None

# Environment variables
raw_env = [
    'PYTHONPATH=/root/projects/viral-together',
    'VIRTUAL_ENV=/root/projects/viral-together/viralt',
]

# Preload app for better performance
preload_app = True

# Worker timeout
graceful_timeout = 30

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190