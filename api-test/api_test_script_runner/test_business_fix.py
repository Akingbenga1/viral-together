#!/usr/bin/env python3
"""
Quick test to verify business API fixes
"""

import requests
import json
import time

def test_business_api():
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    # Login
    print("🔐 Logging in...")
    
    # Get database authentication credentials from user
    username = input("Enter database authentication username: ")
    password = input("Enter database authentication password: ")
    
    response = session.post(
        f"{base_url}/auth/token",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    auth_token = response.json().get("access_token")
    print(f"✅ Login successful")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test 1: Get existing business
    print("\n1️⃣ Testing GET business by ID...")
    response = session.get(f"{base_url}/business/get_business_by_id/12", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Business found: {response.json().get('name', 'Unknown')}")
    
    # Test 2: List all businesses
    print("\n2️⃣ Testing list all businesses...")
    response = session.get(f"{base_url}/business/get_all", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        businesses = response.json()
        print(f"   ✅ Found {len(businesses)} businesses")
    
    # Test 3: Search by base country
    print("\n3️⃣ Testing search by base country...")
    response = session.get(f"{base_url}/business/search/by_base_country?country_id=1", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        businesses = response.json()
        print(f"   ✅ Found {len(businesses)} businesses in country 1")
    
    print("\n✅ Business API tests completed!")

if __name__ == "__main__":
    test_business_api()
