#!/usr/bin/env python3
"""
Test script for promotion endpoints
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBa2luZ2JlbmdhIiwiZXhwIjoxNzUzOTYxNDc2fQ.7bdwEsF8ZXe3CoodX-gHriykZikN4qa4xB6BdWn8KJs"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def test_create_promotion():
    """Test creating a new promotion"""
    print("Testing: Create Promotion")
    
    data = {
        "business_id": 1,
        "promotion_name": "Test Promotion API",
        "promotion_item": "Test Item",
        "description": "Test description for API testing",
        "start_date": "2024-06-01T00:00:00",
        "end_date": "2024-06-30T00:00:00",
        "discount": 10.0,
        "budget": 4000.0,
        "spent_amount": 0.0,
        "status": "pending",
        "target_audience": "Young Adults",
        "social_media_platform_id": 9
    }
    
    try:
        response = requests.post(f"{BASE_URL}/promotions/", json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Promotion created successfully!")
            print(f"   ID: {result.get('id')}")
            print(f"   Name: {result.get('promotion_name')}")
            print(f"   Status: {result.get('status')}")
            return result.get('id')
        else:
            print(f"ERROR: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def test_get_promotion(promotion_id):
    """Test getting a promotion by ID"""
    print(f"\nTesting: Get Promotion {promotion_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/promotions/{promotion_id}", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Promotion retrieved successfully!")
            print(f"   Name: {result.get('promotion_name')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Budget: {result.get('budget')}")
            print(f"   Spent: {result.get('spent_amount')}")
        else:
            print(f"ERROR: {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def test_update_promotion_status(promotion_id):
    """Test updating promotion status"""
    print(f"\nTesting: Update Promotion Status {promotion_id}")
    
    data = {"status": "active"}
    
    try:
        response = requests.patch(f"{BASE_URL}/promotions/{promotion_id}/status", json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Status updated successfully!")
            print(f"   New Status: {result.get('status')}")
        else:
            print(f"ERROR: {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def test_update_promotion_spent(promotion_id):
    """Test updating promotion spent amount"""
    print(f"\nTesting: Update Promotion Spent Amount {promotion_id}")
    
    data = {"spent_amount": 1500.0}
    
    try:
        response = requests.patch(f"{BASE_URL}/promotions/{promotion_id}/spent", json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Spent amount updated successfully!")
            print(f"   Spent Amount: {result.get('spent_amount')}")
        else:
            print(f"ERROR: {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def test_get_promotion_influencers(promotion_id):
    """Test getting promotion influencers"""
    print(f"\nTesting: Get Promotion Influencers {promotion_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/promotions/{promotion_id}/influencers", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Influencers retrieved successfully!")
            print(f"   Number of influencers: {len(result)}")
            for influencer in result:
                print(f"   - {influencer.get('influencer_name')} (Status: {influencer.get('collaboration_status')})")
        else:
            print(f"ERROR: {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def test_list_promotions():
    """Test listing all promotions"""
    print(f"\nTesting: List All Promotions")
    
    try:
        response = requests.get(f"{BASE_URL}/promotions", headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Promotions listed successfully!")
            print(f"   Number of promotions: {len(result)}")
            for promotion in result:
                print(f"   - {promotion.get('promotion_name')} (Status: {promotion.get('status')})")
        else:
            print(f"ERROR: {response.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    print("Starting Promotion API Tests")
    print("=" * 50)
    
    # Test 1: Create promotion
    promotion_id = test_create_promotion()
    
    if promotion_id:
        # Test 2: Get promotion
        test_get_promotion(promotion_id)
        
        # Test 3: Update status
        test_update_promotion_status(promotion_id)
        
        # Test 4: Update spent amount
        test_update_promotion_spent(promotion_id)
        
        # Test 5: Get influencers (will be empty initially)
        test_get_promotion_influencers(promotion_id)
    
    # Test 6: List all promotions
    test_list_promotions()
    
    print("\n" + "=" * 50)
    print("Promotion API Tests Completed")
