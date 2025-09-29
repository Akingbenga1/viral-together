# Environment Variables Guide

This guide explains all the environment variables needed for the Viral Together application, including the new distributed task queue system.

## 🚀 Quick Start

1. Copy `env_example_template.txt` to `.env`
2. Fill in your actual values
3. Start Redis server: `redis-server`
4. Start Celery worker: `python scripts/start_celery_worker.py`
5. Start the FastAPI application

## 📋 Environment Variables by Category

### 🔧 Core Database Configuration
```bash
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/viral_together
TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/viral_together_test
SECRET_KEY=your-secret-key-here
```

### 🚀 Distributed Task Queue (Celery + Redis)
**NEW**: These are the key variables for the distributed task queue system:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Celery Task Configuration
CELERY_TASK_TIME_LIMIT=1800          # 30 minutes max task time
CELERY_TASK_SOFT_TIME_LIMIT=1500     # 25 minutes soft limit
CELERY_WORKER_PREFETCH_MULTIPLIER=1  # Worker prefetch multiplier
CELERY_RESULT_EXPIRES=3600           # 1 hour result expiration
CELERY_WORKER_MAX_TASKS_PER_CHILD=50 # Max tasks per worker process
```

### 🤖 AI Agent Configuration
```bash
# Basic AI Agent Settings
AI_AGENTS_ENABLED=true
AI_AGENT_TOOL_CALLING_ENABLED=true
AI_AGENT_MCP_ENABLED=true
AI_AGENT_MAX_TOKENS=2000
AI_AGENT_TEMPERATURE=0.7
AI_AGENT_TOP_P=0.9

# AI Agent Orchestration
AI_AGENT_ORCHESTRATION_MODE=llm
AI_AGENT_LLM_ORCHESTRATION_ENABLED=true
AI_AGENT_DATABASE_ORCHESTRATION_ENABLED=true
AI_AGENT_TASK_COMPLEXITY_THRESHOLD=medium
AI_AGENT_ORCHESTRATION_MODEL=gemma3:1b

# Enhanced AI Agents
ENHANCED_AI_AGENTS_ENABLED=true
REAL_TIME_DATA_CACHE_TTL=300
MAX_CONCURRENT_AGENT_REQUESTS=10
```

### 🦙 Ollama Configuration
```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

### 🔌 MCP Server Configuration
```bash
MCP_CONFIG_PATH=mcp_config.json
MCP_SERVERS_ENABLED=true

# Multi-Source Data Configuration
MCP_ENABLED=false
DIRECT_API_ENABLED=false
THIRD_PARTY_ENABLED=false
```

### 🌐 Web Search Configuration
```bash
WEB_SEARCH_ENABLED=false
WEB_SEARCH_API_KEY=your-web-search-api-key
WEB_SEARCH_ENGINE=duckduckgo
WEB_SEARCH_ENGINE_ID=your-search-engine-id
```

### 📧 Notification System
```bash
NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=true
TWITTER_NOTIFICATIONS_ENABLED=true
WEBSOCKET_ENABLED=true
```

### 📍 Location Services
```bash
LOCATION_SERVICE_PROVIDER=openstreetmap
DEFAULT_SEARCH_RADIUS_KM=50
MAX_SEARCH_RADIUS_KM=500
OSM_USER_AGENT=ViralTogether/1.0
OSM_BASE_URL=https://nominatim.openstreetmap.org
```

## 🆕 New Environment Variables for Distributed Task Queue

The following environment variables are **NEW** and essential for the distributed task queue system:

### Core Redis/Celery Variables
- `REDIS_URL` - Redis server URL for task queue
- `CELERY_BROKER_URL` - Celery message broker URL
- `CELERY_RESULT_BACKEND` - Celery result backend URL

### Task Configuration Variables
- `CELERY_TASK_TIME_LIMIT` - Maximum time a task can run (seconds)
- `CELERY_TASK_SOFT_TIME_LIMIT` - Soft time limit for graceful shutdown
- `CELERY_WORKER_PREFETCH_MULTIPLIER` - How many tasks a worker can prefetch
- `CELERY_RESULT_EXPIRES` - How long to keep task results (seconds)
- `CELERY_WORKER_MAX_TASKS_PER_CHILD` - Max tasks before worker restart

## 🚀 Setup Instructions

### 1. Install Redis
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://redis.io/download
```

### 2. Start Redis
```bash
redis-server
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Celery Worker
```bash
python scripts/start_celery_worker.py
```

### 5. Start Celery Flower (Optional - for monitoring)
```bash
python scripts/start_celery_flower.py
```

### 6. Start FastAPI Application
```bash
uvicorn app.main:app --reload
```

## 🔍 Monitoring and Debugging

### Check Redis Connection
```bash
redis-cli ping
# Should return: PONG
```

### Check Celery Worker Status
```bash
celery -A app.core.celery_app inspect active
```

### Monitor Tasks with Flower
- Open browser to `http://localhost:5555`
- View active tasks, worker status, and task history

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Ensure Redis is running: `redis-server`
   - Check Redis URL in `.env` file

2. **Celery Worker Not Starting**
   - Check Redis connection
   - Verify all dependencies are installed
   - Check worker logs for errors

3. **Tasks Not Processing**
   - Ensure Celery worker is running
   - Check task queue configuration
   - Verify task routing in `celery_app.py`

### Debug Commands
```bash
# Check Redis
redis-cli info

# Check Celery workers
celery -A app.core.celery_app inspect stats

# Check task queues
celery -A app.core.celery_app inspect active_queues
```

## 📊 Performance Tuning

### Worker Configuration
- Adjust `CELERY_WORKER_PREFETCH_MULTIPLIER` based on task complexity
- Set `CELERY_WORKER_MAX_TASKS_PER_CHILD` to prevent memory leaks
- Configure `CELERY_TASK_TIME_LIMIT` based on your longest tasks

### Redis Configuration
- Monitor Redis memory usage
- Configure Redis persistence if needed
- Set appropriate Redis timeout values

## 🔒 Security Considerations

- Use strong passwords for Redis in production
- Configure Redis authentication
- Use SSL/TLS for Redis connections in production
- Restrict Redis access to application servers only

## 📈 Production Deployment

### Environment Variables for Production
```bash
# Production Redis (with authentication)
REDIS_URL=redis://:password@redis-server:6379/0
CELERY_BROKER_URL=redis://:password@redis-server:6379/0
CELERY_RESULT_BACKEND=redis://:password@redis-server:6379/0

# Production Database
DATABASE_URL=postgresql+asyncpg://user:pass@db-server:5432/viral_together

# Security
SECRET_KEY=your-very-secure-secret-key
```

### Production Celery Configuration
- Use multiple worker processes
- Configure task routing for different queues
- Set up monitoring and alerting
- Configure task retry policies
- Set up task result cleanup

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Celery Flower Monitoring](https://flower.readthedocs.io/)
