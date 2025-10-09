#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import requests
import json

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_endpoint():
    """Test the promotions-with-collaborations endpoint for owner_id 27"""
    
    url = "http://localhost:8000/business/promotions-with-collaborations"
    
    # Test with user_id = 27
    payload = {"business_owner_id": 27}
    
    print("="*80)
    print("TESTING ENDPOINT FOR BUSINESS OWNER ID = 27")
    print("="*80)
    print(f"\n🔄 POST Request to: {url}")
    print(f"📦 Request Body: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"✅ HTTP Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 RESPONSE DATA:")
            print(f"   Total Promotions Received: {len(data)}")
            print()
            
            if len(data) == 0:
                print("❌ ERROR: Expected promotions but received empty array!")
                print("   Database shows owner 27 has:")
                print("   - Business ID 29: 'Tech Innovators Inc 20251005_082843'")
                print("   - Promotion ID 51: 'Good resource catchig' (1 collaboration)")
                return
            
            # Group by business_id
            business_groups = {}
            for promo in data:
                bid = promo.get('business_id')
                if bid not in business_groups:
                    business_groups[bid] = []
                business_groups[bid].append(promo)
            
            print(f"🏢 Businesses Found: {len(business_groups)}")
            print(f"   Business IDs: {sorted(business_groups.keys())}\n")
            
            total_collabs = 0
            for bid in sorted(business_groups.keys()):
                promos = business_groups[bid]
                print(f"📍 Business ID {bid}:")
                print(f"   Promotions: {len(promos)}\n")
                
                for promo in promos:
                    stats = promo.get('collaboration_stats', {})
                    total = stats.get('total', 0)
                    total_collabs += total
                    
                    print(f"   ▸ Promotion: {promo.get('promotion_name')}")
                    print(f"     UUID: {promo.get('uuid', 'N/A')[:8] if promo.get('uuid') else 'N/A'}")
                    print(f"     Full UUID: {promo.get('uuid', 'N/A')}")
                    print(f"     Promotion ID: {promo.get('id')}")
                    print(f"     Collaborations:")
                    print(f"       • Total: {stats.get('total', 0)}")
                    print(f"       • Active: {stats.get('active', 0)}")
                    print(f"       • Approved: {stats.get('approved', 0)}")
                    print(f"       • Pending: {stats.get('pending', 0)}")
                    print(f"       • Rejected: {stats.get('rejected', 0)}")
                    print()
            
            print("="*80)
            print(f"✅ SUCCESS: Endpoint returned {len(data)} promotion(s) with {total_collabs} total collaboration(s)")
            print("="*80)
            
        else:
            print(f"❌ ERROR Response:")
            print(f"   Status: {response.status_code}")
            print(f"   Body: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    test_endpoint()

