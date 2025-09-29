@echo off
echo ========================================
echo Celery & Redis Monitoring Scripts
echo ========================================
echo.
echo Choose monitoring option:
echo 1. Quick Status Check (once)
echo 2. Continuous Monitoring (5 second intervals)
echo 3. Continuous Monitoring (10 second intervals)
echo 4. Continuous Monitoring (30 second intervals)
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Running quick status check...
    python scripts\quick_monitor.py
    pause
) else if "%choice%"=="2" (
    echo Starting continuous monitoring (5s intervals)...
    echo Press Ctrl+C to stop
    python scripts\monitor_celery_redis.py --interval 5
) else if "%choice%"=="3" (
    echo Starting continuous monitoring (10s intervals)...
    echo Press Ctrl+C to stop
    python scripts\monitor_celery_redis.py --interval 10
) else if "%choice%"=="4" (
    echo Starting continuous monitoring (30s intervals)...
    echo Press Ctrl+C to stop
    python scripts\monitor_celery_redis.py --interval 30
) else if "%choice%"=="5" (
    echo Goodbye!
    exit
) else (
    echo Invalid choice. Please run the script again.
    pause
)
