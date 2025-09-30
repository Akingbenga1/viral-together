#!/usr/bin/env python3
"""
Test script for the orchestrated analysis endpoint
"""
import requests
import json
import time

def test_orchestrated_analysis():
    """Test the orchestrated analysis endpoint"""
    url = 'http://localhost:8000/recommendations/trigger-analysis/13'
    print('Testing orchestrated analysis endpoint...')
    print(f'URL: {url}')

    try:
        response = requests.post(url)
        print(f'Status Code: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'Task ID: {data.get("task_id")}')
            print(f'Status: {data.get("status")}')
            print(f'Message: {data.get("message")}')
            print(f'Influencer ID: {data.get("influencer_id")}')
            
            # Wait a bit and check task status
            if data.get("task_id"):
                print(f'\nWaiting 15 seconds to check task status...')
                time.sleep(15)
                check_task_status(data.get("task_id"))
        else:
            print(f'Error: {response.text}')
            
    except Exception as e:
        print(f'Request failed: {e}')

def check_task_status(task_id):
    """Check the status of a task"""
    try:
        # Check task status in database
        url = f'http://localhost:8000/api/task-status/{task_id}'
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f'Task Status: {data.get("status")}')
            print(f'Task Message: {data.get("message")}')
            if data.get("result"):
                print(f'Task Result: {data.get("result")[:200]}...')
        else:
            print(f'Failed to get task status: {response.text}')
            
    except Exception as e:
        print(f'Failed to check task status: {e}')

if __name__ == "__main__":
    test_orchestrated_analysis()