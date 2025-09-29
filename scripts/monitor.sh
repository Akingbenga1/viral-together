#!/bin/bash

echo "========================================"
echo "Celery & Redis Monitoring Scripts"
echo "========================================"
echo ""
echo "Choose monitoring option:"
echo "1. Quick Status Check (once)"
echo "2. Continuous Monitoring (5 second intervals)"
echo "3. Continuous Monitoring (10 second intervals)"
echo "4. Continuous Monitoring (30 second intervals)"
echo "5. Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "Running quick status check..."
        python scripts/quick_monitor.py
        ;;
    2)
        echo "Starting continuous monitoring (5s intervals)..."
        echo "Press Ctrl+C to stop"
        python scripts/monitor_celery_redis.py --interval 5
        ;;
    3)
        echo "Starting continuous monitoring (10s intervals)..."
        echo "Press Ctrl+C to stop"
        python scripts/monitor_celery_redis.py --interval 10
        ;;
    4)
        echo "Starting continuous monitoring (30s intervals)..."
        echo "Press Ctrl+C to stop"
        python scripts/monitor_celery_redis.py --interval 30
        ;;
    5)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac
