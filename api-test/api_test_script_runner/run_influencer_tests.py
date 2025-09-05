#!/usr/bin/env python3
"""
Automated API Test Runner for Influencer Endpoints
This script automatically tests all endpoints defined in influencers.http
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    name: str
    method: str
    endpoint: str
    status_code: int
    response_time: float
    success: bool
    error: str = None
    response_data: Any = None

class InfluencerAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results: List[TestResult] = []
        
    def login(self) -> bool:
        """Login to get authentication token"""
        try:
            print("🔐 Logging in...")
            
            # Get database authentication credentials from user
            username = input("Enter database authentication username: ")
            password = input("Enter database authentication password: ")
            
            response = self.session.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                print(f"✅ Login successful - Token: {self.auth_token[:20]}...")
                return True
            else:
                print(f"❌ Login failed - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Login error: {e}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    expected_status: int = 200) -> TestResult:
        """Make HTTP request and return test result"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if data:
            headers["Content-Type"] = "application/json"
        
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            response_time = time.time() - start_time
            success = response.status_code == expected_status
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = response.text
            
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time=response_time,
                success=success,
                response_data=response_data
            )
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all influencer API tests"""
        print("🚀 Starting Influencer API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Authenticated endpoints
        self._run_test_1_create_influencer()
        self._run_test_2_get_influencer_by_id()
        self._run_test_3_update_influencer()
        self._run_test_4_delete_influencer()
        self._run_test_5_list_all_influencers()
        self._run_test_6_search_by_base_country()
        self._run_test_7_search_by_collaboration_country()
        
        # Public endpoints (no authentication needed)
        self._run_test_8_create_public_influencer()
        self._run_test_9_search_by_criteria_public()
        
        return self.test_results
    
    def _run_test_1_create_influencer(self):
        """Test 1: Create a New Influencer (Authenticated)"""
        print("\n1️⃣ Creating New Influencer (Authenticated)...")
        create_data = {
            "bio": "A passionate influencer in the tech space.",
            "profile_image_url": "https://example.com/profile.jpg",
            "website_url": "https://example.com",
            "languages": "English, Spanish",
            "availability": True,
            "rate_per_post": 150.0,
            "total_posts": 50,
            "growth_rate": 10,
            "successful_campaigns": 5,
            "user_id": 1,
            "base_country_id": 1,
            "collaboration_country_ids": [2, 3, 4]
        }
        result = self.make_request("POST", "/influencer/create_influencer", create_data, expected_status=201)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_get_influencer_by_id(self):
        """Test 2: Get Influencer by ID (Authenticated)"""
        print("\n2️⃣ Getting Influencer by ID (Authenticated)...")
        result = self.make_request("GET", "/influencer/get_influencer/1")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_update_influencer(self):
        """Test 3: Update an Influencer by ID (Authenticated - Admin Only)"""
        print("\n3️⃣ Updating Influencer (Admin Only)...")
        update_data = {
            "bio": "Updated Influencer Bio",
            "base_country_id": 1,
            "collaboration_country_ids": [5, 6]
        }
        result = self.make_request("PUT", "/influencer/update_influencer/1", update_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_delete_influencer(self):
        """Test 4: Delete an Influencer by ID (Authenticated - Admin Only)"""
        print("\n4️⃣ Deleting Influencer (Admin Only)...")
        result = self.make_request("DELETE", "/influencer/remove_influencer/1", expected_status=204)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_5_list_all_influencers(self):
        """Test 5: List All Influencers (Authenticated)"""
        print("\n5️⃣ Listing All Influencers (Authenticated)...")
        result = self.make_request("GET", "/influencer/list")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_6_search_by_base_country(self):
        """Test 6: Search Influencers by Base Country (Authenticated)"""
        print("\n6️⃣ Searching by Base Country (Authenticated)...")
        result = self.make_request("GET", "/influencer/search/by_base_country?country_id=1")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_7_search_by_collaboration_country(self):
        """Test 7: Search Influencers by Collaboration Country (Authenticated)"""
        print("\n7️⃣ Searching by Collaboration Country (Authenticated)...")
        result = self.make_request("GET", "/influencer/search/by_collaboration_country?country_id=5")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_8_create_public_influencer(self):
        """Test 8: Create Public Influencer Profile (Unauthenticated)"""
        print("\n8️⃣ Creating Public Influencer Profile (Unauthenticated)...")
        public_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith_influencer",
            "email": "jane.smith@example.com",
            "bio": "A passionate influencer in the lifestyle space.",
            "profile_image_url": "https://example.com/jane-profile.jpg",
            "website_url": "https://janesmith.com",
            "languages": "English, French",
            "availability": True,
            "rate_per_post": 200.0,
            "total_posts": 75,
            "growth_rate": 15,
            "successful_campaigns": 8,
            "base_country_id": 2,
            "collaboration_country_ids": [1, 3, 4]
        }
        result = self.make_request("POST", "/influencer/create_public", public_data, expected_status=201)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_search_by_criteria_public(self):
        """Test 9: Search Influencers by Criteria (Unauthenticated)"""
        print("\n9️⃣ Searching by Criteria (Unauthenticated)...")
        search_data = {
            "country_ids": [1, 2, 3],
            "industry": "Technology",
            "social_media_platform": "instagram"
        }
        result = self.make_request("POST", "/influencer/search/by_criteria", search_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Get Non-existent Influencer
        print("\n❌ Getting Non-existent Influencer...")
        result = self.make_request("GET", "/influencer/get_influencer/999", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Create Influencer with Invalid Data
        print("\n❌ Creating Influencer with Invalid Data...")
        invalid_data = {
            "bio": "",
            "rate_per_post": -100,  # Invalid negative rate
            "user_id": 999  # Non-existent user
        }
        result = self.make_request("POST", "/influencer/create_influencer", invalid_data, expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Update Non-existent Influencer
        print("\n❌ Updating Non-existent Influencer...")
        update_data = {
            "bio": "This should fail"
        }
        result = self.make_request("PUT", "/influencer/update_influencer/999", update_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 4: Delete Non-existent Influencer
        print("\n❌ Deleting Non-existent Influencer...")
        result = self.make_request("DELETE", "/influencer/remove_influencer/999", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 5: Create Public Influencer with Duplicate Username
        print("\n❌ Creating Public Influencer with Duplicate Username...")
        duplicate_data = {
            "first_name": "Duplicate",
            "last_name": "User",
            "username": "Akingbenga",  # This username already exists
            "email": "duplicate@example.com",
            "bio": "This should fail due to duplicate username",
            "profile_image_url": "https://example.com/duplicate.jpg",
            "website_url": "https://duplicate.com",
            "languages": "English",
            "availability": True,
            "rate_per_post": 100.0,
            "total_posts": 10,
            "growth_rate": 5,
            "successful_campaigns": 2,
            "base_country_id": 1,
            "collaboration_country_ids": [2]
        }
        result = self.make_request("POST", "/influencer/create_public", duplicate_data, expected_status=400)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.success:
                    print(f"   - {result.name}: {result.status_code} {result.error or ''}")
        
        # Calculate average response time
        avg_response_time = sum(result.response_time for result in self.test_results) / total_tests
        print(f"\n⏱️  Average Response Time: {avg_response_time:.2f}s")

def main():
    """Main function to run the tests"""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_influencer_tests.py [base_url] [test_number]")
        print("  python run_influencer_tests.py                    # Run all tests")
        print("  python run_influencer_tests.py http://localhost:8000  # Run all tests with custom URL")
        print("  python run_influencer_tests.py http://localhost:8000 1  # Run only test 1")
        print("\nAvailable test numbers:")
        print("  1  - Create Influencer (Authenticated)")
        print("  2  - Get Influencer by ID (Authenticated)")
        print("  3  - Update Influencer (Admin Only)")
        print("  4  - Delete Influencer (Admin Only)")
        print("  5  - List All Influencers (Authenticated)")
        print("  6  - Search by Base Country (Authenticated)")
        print("  7  - Search by Collaboration Country (Authenticated)")
        print("  8  - Create Public Influencer (Unauthenticated)")
        print("  9  - Search by Criteria (Unauthenticated)")
        sys.exit(1)
    
    # Parse arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_number = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = InfluencerAPITester(base_url)
    
    # Login first
    if not tester.login():
        print("❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Run specific test or all tests
    if test_number:
        print(f"🧪 Running Test {test_number} only...")
        print(f"📍 Base URL: {base_url}")
        print("=" * 60)
        
        # Map test numbers to methods
        test_methods = {
            "1": tester._run_test_1_create_influencer,
            "2": tester._run_test_2_get_influencer_by_id,
            "3": tester._run_test_3_update_influencer,
            "4": tester._run_test_4_delete_influencer,
            "5": tester._run_test_5_list_all_influencers,
            "6": tester._run_test_6_search_by_base_country,
            "7": tester._run_test_7_search_by_collaboration_country,
            "8": tester._run_test_8_create_public_influencer,
            "9": tester._run_test_9_search_by_criteria_public,
        }
        
        if test_number in test_methods:
            test_methods[test_number]()
        else:
            print(f"❌ Invalid test number: {test_number}")
            print("Available test numbers: 1, 2, 3, 4, 5, 6, 7, 8, 9")
            sys.exit(1)
    else:
        # Run all tests
        tester.run_all_tests()
        # Run error tests
        tester.run_error_tests()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()
