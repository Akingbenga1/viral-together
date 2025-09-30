import requests
import json

# Test the trigger analysis endpoint
url = 'http://localhost:8000/recommendations/trigger-analysis/13'
headers = {'Content-Type': 'application/json'}

print('Testing trigger analysis endpoint after fix...')
print(f'URL: {url}')

try:
    response = requests.post(url, headers=headers, timeout=30)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print('Success!')
        print(f'Task ID: {result.get("task_id")}')
        print(f'Status: {result.get("status")}')
        print(f'Message: {result.get("message")}')
        print(f'Influencer ID: {result.get("influencer_id")}')
    else:
        print(f'Error: {response.status_code}')
        print(f'Response: {response.text}')
        
except Exception as e:
    print(f'Request failed: {e}')
