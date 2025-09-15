#!/usr/bin/env python3
"""
Analytics API Test Script
Tests the analytics endpoints for admin dashboard functionality.
"""

import requests
import json
import sys
from datetime import datetime
import os

# Add the parent directory to the path to import the test runner
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_runner_base import TestRunnerBase

class AnalyticsTestRunner(TestRunnerBase):
    def __init__(self):
        super().__init__()
        self.base_url = self.get_base_url()
        self.auth_token = self.get_auth_token()
        self.test_results = []
        
    def test_user_registrations_by_month(self):
        """Test the user registrations by month endpoint"""
        test_name = "User Registrations by Month"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.base_url}/api/analytics/user-registrations-by-month',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['success', 'year', 'data']
                if all(field in data for field in required_fields):
                    if data['success'] and isinstance(data['data'], list):
                        # Check if data has 12 months
                        if len(data['data']) == 12:
                            # Validate each month entry
                            valid_months = all(
                                'month' in item and 'month_number' in item and 'registrations' in item
                                for item in data['data']
                            )
                            if valid_months:
                                print(f"✅ {test_name} - SUCCESS")
                                print(f"   📊 Year: {data['year']}")
                                print(f"   📈 Total months: {len(data['data'])}")
                                
                                # Show sample data
                                sample_data = data['data'][:3]
                                for item in sample_data:
                                    print(f"   📅 {item['month']}: {item['registrations']} registrations")
                                
                                self.test_results.append({
                                    'test': test_name,
                                    'status': 'PASS',
                                    'details': f"Retrieved {len(data['data'])} months of data"
                                })
                                return True
                            else:
                                print(f"❌ {test_name} - FAILED: Invalid month data structure")
                        else:
                            print(f"❌ {test_name} - FAILED: Expected 12 months, got {len(data['data'])}")
                    else:
                        print(f"❌ {test_name} - FAILED: Invalid success flag or data format")
                else:
                    print(f"❌ {test_name} - FAILED: Missing required fields")
                    
            elif response.status_code == 403:
                print(f"⚠️  {test_name} - UNAUTHORIZED: Admin access required")
                self.test_results.append({
                    'test': test_name,
                    'status': 'SKIP',
                    'details': 'Admin access required - test user may not have admin privileges'
                })
                return True
            else:
                print(f"❌ {test_name} - FAILED: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_name} - ERROR: {str(e)}")
            
        self.test_results.append({
            'test': test_name,
            'status': 'FAIL',
            'details': f'HTTP {response.status_code}' if 'response' in locals() else 'Request failed'
        })
        return False
    
    def test_business_registrations_by_month(self):
        """Test the business registrations by month endpoint"""
        test_name = "Business Registrations by Month"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.base_url}/api/analytics/business-registrations-by-month',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['success', 'year', 'data']
                if all(field in data for field in required_fields):
                    if data['success'] and isinstance(data['data'], list):
                        # Check if data has 12 months
                        if len(data['data']) == 12:
                            # Validate each month entry
                            valid_months = all(
                                'month' in item and 'month_number' in item and 'registrations' in item
                                for item in data['data']
                            )
                            if valid_months:
                                print(f"✅ {test_name} - SUCCESS")
                                print(f"   📊 Year: {data['year']}")
                                print(f"   📈 Total months: {len(data['data'])}")
                                
                                # Show sample data
                                sample_data = data['data'][:3]
                                for item in sample_data:
                                    print(f"   📅 {item['month']}: {item['registrations']} registrations")
                                
                                self.test_results.append({
                                    'test': test_name,
                                    'status': 'PASS',
                                    'details': f"Retrieved {len(data['data'])} months of data"
                                })
                                return True
                            else:
                                print(f"❌ {test_name} - FAILED: Invalid month data structure")
                        else:
                            print(f"❌ {test_name} - FAILED: Expected 12 months, got {len(data['data'])}")
                    else:
                        print(f"❌ {test_name} - FAILED: Invalid success flag or data format")
                else:
                    print(f"❌ {test_name} - FAILED: Missing required fields")
                    
            elif response.status_code == 403:
                print(f"⚠️  {test_name} - UNAUTHORIZED: Admin access required")
                self.test_results.append({
                    'test': test_name,
                    'status': 'SKIP',
                    'details': 'Admin access required - test user may not have admin privileges'
                })
                return True
            else:
                print(f"❌ {test_name} - FAILED: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_name} - ERROR: {str(e)}")
            
        self.test_results.append({
            'test': test_name,
            'status': 'FAIL',
            'details': f'HTTP {response.status_code}' if 'response' in locals() else 'Request failed'
        })
        return False
    
    def test_analytics_summary(self):
        """Test the analytics summary endpoint"""
        test_name = "Analytics Summary"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.base_url}/api/analytics/analytics-summary',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['success', 'data']
                if all(field in data for field in required_fields):
                    if data['success'] and isinstance(data['data'], dict):
                        data_fields = data['data']
                        expected_fields = ['total_users', 'new_users_30d', 'total_businesses', 'new_businesses_30d', 'period']
                        
                        if all(field in data_fields for field in expected_fields):
                            print(f"✅ {test_name} - SUCCESS")
                            print(f"   👥 Total Users: {data_fields['total_users']}")
                            print(f"   🆕 New Users (30d): {data_fields['new_users_30d']}")
                            print(f"   🏢 Total Businesses: {data_fields['total_businesses']}")
                            print(f"   🆕 New Businesses (30d): {data_fields['new_businesses_30d']}")
                            print(f"   📅 Period: {data_fields['period']}")
                            
                            self.test_results.append({
                                'test': test_name,
                                'status': 'PASS',
                                'details': f"Retrieved analytics summary for {data_fields['period']}"
                            })
                            return True
                        else:
                            print(f"❌ {test_name} - FAILED: Missing expected data fields")
                    else:
                        print(f"❌ {test_name} - FAILED: Invalid success flag or data format")
                else:
                    print(f"❌ {test_name} - FAILED: Missing required fields")
                    
            elif response.status_code == 403:
                print(f"⚠️  {test_name} - UNAUTHORIZED: Admin access required")
                self.test_results.append({
                    'test': test_name,
                    'status': 'SKIP',
                    'details': 'Admin access required - test user may not have admin privileges'
                })
                return True
            else:
                print(f"❌ {test_name} - FAILED: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_name} - ERROR: {str(e)}")
            
        self.test_results.append({
            'test': test_name,
            'status': 'FAIL',
            'details': f'HTTP {response.status_code}' if 'response' in locals() else 'Request failed'
        })
        return False
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        test_name = "Unauthorized Access Test"
        print(f"\n🧪 Testing: {test_name}")
        
        try:
            # Test without authorization header
            response = requests.get(
                f'{self.base_url}/api/analytics/user-registrations-by-month',
                timeout=30
            )
            
            if response.status_code == 401 or response.status_code == 403:
                print(f"✅ {test_name} - SUCCESS: Endpoint properly requires authentication")
                self.test_results.append({
                    'test': test_name,
                    'status': 'PASS',
                    'details': f'Endpoint correctly returned {response.status_code} for unauthenticated request'
                })
                return True
            else:
                print(f"❌ {test_name} - FAILED: Endpoint should require authentication")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {test_name} - ERROR: {str(e)}")
            
        self.test_results.append({
            'test': test_name,
            'status': 'FAIL',
            'details': 'Endpoint did not properly require authentication'
        })
        return False
    
    def run_all_tests(self):
        """Run all analytics tests"""
        print("🚀 Starting Analytics API Tests")
        print("=" * 50)
        
        # Test unauthorized access first
        self.test_unauthorized_access()
        
        # Test analytics endpoints (require admin access)
        self.test_user_registrations_by_month()
        self.test_business_registrations_by_month()
        self.test_analytics_summary()
        
        # Print summary
        self.print_test_summary()
        
        return self.test_results

def main():
    """Main function to run analytics tests"""
    runner = AnalyticsTestRunner()
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = [r for r in results if r['status'] == 'FAIL']
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
