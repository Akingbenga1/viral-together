#!/usr/bin/env python3
"""
Automated API Test Runner for Promotion Endpoints
This script automatically tests all endpoints defined in promotion.http
"""

import requests
import json
import time
import sys
import getpass
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

class PromotionAPITester:
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
            password = getpass.getpass("Enter database authentication password: ")
            
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
                    expected_status: int = 200, max_retries: int = 2) -> TestResult:
        """Make HTTP request and return test result with retry logic"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if data:
            headers["Content-Type"] = "application/json"
        
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
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
                
                # If we get a 429 (rate limit), wait and retry
                if response.status_code == 429 and attempt < max_retries:
                    print(f"   ⏳ Rate limited, waiting 2 seconds before retry {attempt + 1}/{max_retries + 1}...")
                    time.sleep(2)
                    continue
                
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
                
                # If it's a connection error and we have retries left, try again
                if "Connection" in str(e) and attempt < max_retries:
                    print(f"   🔄 Connection error, retrying {attempt + 1}/{max_retries + 1}...")
                    time.sleep(1)
                    continue
                
                return TestResult(
                    name=f"{method} {endpoint}",
                    method=method,
                    endpoint=endpoint,
                    status_code=0,
                    response_time=response_time,
                    success=False,
                    error=str(e)
                )
        
        # This should never be reached, but just in case
        return TestResult(
            name=f"{method} {endpoint}",
            method=method,
            endpoint=endpoint,
            status_code=0,
            response_time=time.time() - start_time,
            success=False,
            error="Max retries exceeded"
        )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all promotion API tests"""
        print("🚀 Starting Promotion API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Promotion CRUD endpoints
        self._run_test_1_create_promotion()
        self._run_test_2_get_promotion()
        self._run_test_3_update_promotion()
        self._run_test_4_delete_promotion()
        self._run_test_5_list_promotions()
        
        # Collaboration interest endpoints
        self._run_test_6_show_interest_complete()
        self._run_test_7_show_interest_no_amount()
        self._run_test_8_show_interest_minimal()
        self._run_test_9_show_interest_custom_type()
        
        return self.test_results
    
    def _run_test_1_create_promotion(self):
        """Test 1: Create a New Promotion"""
        print("\n1️⃣ Creating New Promotion...")
        create_data = {
            "business_id": 1,
            "promotion_name": "Electric Ladder Sweater Test",
            "promotion_item": "Gadget",
            "start_date": "2024-06-01T00:00:00",
            "end_date": "2024-06-30T00:00:00",
            "discount": 10.0,
            "budget": 4000.0,
            "target_audience": "Young Adults",
            "social_media_platform_id": 9
        }
        result = self.make_request("POST", "/promotions/", create_data, expected_status=200)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_get_promotion(self):
        """Test 2: Get Promotion by ID"""
        print("\n2️⃣ Getting Promotion by ID...")
        result = self.make_request("GET", "/promotions/9")  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_update_promotion(self):
        """Test 3: Update a Promotion"""
        print("\n3️⃣ Updating Promotion...")
        update_data = {
            "business_id": 1,
            "promotion_name": "Summer Sale Updated Test",
            "promotion_item": "Electronics",
            "start_date": "2024-06-01T00:00:00",
            "end_date": "2024-06-30T00:00:00",
            "discount": 15.0,
            "budget": 6000.0,
            "target_audience": "Young Adults",
            "social_media_platform_id": 9
        }
        result = self.make_request("PUT", "/promotions/9", update_data)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_delete_promotion(self):
        """Test 4: Delete a Promotion"""
        print("\n4️⃣ Deleting Promotion...")
        result = self.make_request("DELETE", "/promotions/10", expected_status=200)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_5_list_promotions(self):
        """Test 5: List All Promotions"""
        print("\n5️⃣ Listing All Promotions...")
        result = self.make_request("GET", "/promotions")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_6_show_interest_complete(self):
        """Test 6: Show Interest in Promotion (Complete Data)"""
        print("\n6️⃣ Showing Interest (Complete Data)...")
        interest_data = {
            "influencer_id": 1,
            "proposed_amount": 1500.0,
            "collaboration_type": "sponsored_post",
            "deliverables": "6 Instagram posts every day.1 article post per week",
            "message": "Ready to create viral magic together! My engaged audience would be thrilled about this collaboration!"
        }
        result = self.make_request("POST", "/promotions/11/show-interest", interest_data)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_7_show_interest_no_amount(self):
        """Test 7: Show Interest without Proposed Amount"""
        print("\n7️⃣ Showing Interest (No Amount)...")
        interest_data = {
            "influencer_id": 2,
            "collaboration_type": "product_review",
            "deliverables": "Honest review video on TikTok",
            "message": "This product aligns perfectly with my audience!"
        }
        result = self.make_request("POST", "/promotions/12/show-interest", interest_data)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_8_show_interest_minimal(self):
        """Test 8: Show Interest with Minimal Data"""
        print("\n8️⃣ Showing Interest (Minimal Data)...")
        interest_data = {
            "influencer_id": 3,
            "collaboration_type": "brand_ambassador"
        }
        result = self.make_request("POST", "/promotions/13/show-interest", interest_data)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_show_interest_custom_type(self):
        """Test 9: Show Interest with Custom Collaboration Type"""
        print("\n9️⃣ Showing Interest (Custom Type)...")
        interest_data = {
            "influencer_id": 4,
            "proposed_amount": 800.0,
            "collaboration_type": "event_coverage",
            "deliverables": "Live event coverage, 3 posts, highlight reel",
            "message": "I have experience covering similar events and can provide great exposure!"
        }
        result = self.make_request("POST", "/promotions/14/show-interest", interest_data)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Try to Show Interest Twice (Should Fail - Duplicate)
        print("\n❌ Trying to Show Interest Twice (Duplicate)...")
        interest_data = {
            "influencer_id": 1,
            "collaboration_type": "sponsored_post",
            "message": "Trying to submit interest again..."
        }
        result = self.make_request("POST", "/promotions/11/show-interest", interest_data, expected_status=400)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Show Interest in Non-existent Promotion (Should Fail - 404)
        print("\n❌ Showing Interest in Non-existent Promotion...")
        interest_data = {
            "influencer_id": 1,
            "collaboration_type": "sponsored_post"
        }
        result = self.make_request("POST", "/promotions/99999/show-interest", interest_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Show Interest with Non-existent Influencer (Should Fail - 404)
        print("\n❌ Showing Interest with Non-existent Influencer...")
        interest_data = {
            "influencer_id": 99999,
            "collaboration_type": "sponsored_post"
        }
        result = self.make_request("POST", "/promotions/15/show-interest", interest_data, expected_status=404)  # Use existing promotion ID
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 4: Get Non-existent Promotion (Should Fail - 404)
        print("\n❌ Getting Non-existent Promotion...")
        result = self.make_request("GET", "/promotions/99999", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 5: Update Non-existent Promotion (Should Fail - 404)
        print("\n❌ Updating Non-existent Promotion...")
        update_data = {
            "business_id": 1,
            "promotion_name": "This should fail",
            "promotion_item": "Test",
            "start_date": "2024-06-01T00:00:00",
            "end_date": "2024-06-30T00:00:00",
            "social_media_platform_id": 9
        }
        result = self.make_request("PUT", "/promotions/99999", update_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 6: Delete Non-existent Promotion (Should Fail - 404)
        print("\n❌ Deleting Non-existent Promotion...")
        result = self.make_request("DELETE", "/promotions/99999", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 7: Create Promotion with Invalid Business ID (Should Fail - 404)
        print("\n❌ Creating Promotion with Invalid Business ID...")
        create_data = {
            "business_id": 99999,
            "promotion_name": "Invalid Business Test",
            "promotion_item": "Test",
            "start_date": "2024-06-01T00:00:00",
            "end_date": "2024-06-30T00:00:00",
            "social_media_platform_id": 9
        }
        result = self.make_request("POST", "/promotions/", create_data, expected_status=404)
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
        print("  python run_promotion_tests.py [base_url] [test_number]")
        print("  python run_promotion_tests.py                    # Run all tests")
        print("  python run_promotion_tests.py http://localhost:8000  # Run all tests with custom URL")
        print("  python run_promotion_tests.py http://localhost:8000 1  # Run only test 1")
        print("\nAvailable test numbers:")
        print("  1  - Create Promotion")
        print("  2  - Get Promotion by ID")
        print("  3  - Update Promotion")
        print("  4  - Delete Promotion")
        print("  5  - List All Promotions")
        print("  6  - Show Interest (Complete Data)")
        print("  7  - Show Interest (No Amount)")
        print("  8  - Show Interest (Minimal Data)")
        print("  9  - Show Interest (Custom Type)")
        sys.exit(1)
    
    # Parse arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_number = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = PromotionAPITester(base_url)
    
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
            "1": tester._run_test_1_create_promotion,
            "2": tester._run_test_2_get_promotion,
            "3": tester._run_test_3_update_promotion,
            "4": tester._run_test_4_delete_promotion,
            "5": tester._run_test_5_list_promotions,
            "6": tester._run_test_6_show_interest_complete,
            "7": tester._run_test_7_show_interest_no_amount,
            "8": tester._run_test_8_show_interest_minimal,
            "9": tester._run_test_9_show_interest_custom_type,
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
