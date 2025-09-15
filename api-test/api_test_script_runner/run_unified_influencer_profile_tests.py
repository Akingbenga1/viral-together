#!/usr/bin/env python3
"""
Automated API Test Runner for Unified Influencer Profile Endpoints
This script automatically tests all endpoints defined in unified_influencer_profile_tests.http
"""

import requests
import json
import time
import sys
import getpass
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from faker import Faker

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

class UnifiedInfluencerProfileAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results: List[TestResult] = []
        
        # Initialize Faker for generating random data
        self.fake = Faker()
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('unified_influencer_profile_api_tests')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"unified_influencer_profile_api_tests_{timestamp}.log"
        log_path = os.path.join(log_dir, log_filename)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        print(f"📝 Logging to file: {log_path}")
        
    def login(self) -> bool:
        """Login to get authentication token"""
        try:
            print("🔐 Logging in...")
            
            # Get database authentication credentials from user
            username = input("Enter database authentication username: ")
            password = getpass.getpass("Enter database authentication password: ")
            
            url = f"{self.base_url}/auth/token"
            data = {
                "username": username,
                "password": password
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            # Log login request details
            self.logger.info("=" * 80)
            self.logger.info("API REQUEST: POST /auth/token (LOGIN)")
            self.logger.info(f"FULL URL: {url}")
            self.logger.info(f"REQUEST HEADERS: {json.dumps(headers, indent=2)}")
            self.logger.info(f"REQUEST BODY: username={username}&password=***HIDDEN***")
            self.logger.info("-" * 80)
            
            start_time = time.time()
            
            response = self.session.post(
                url,
                data=data,
                headers=headers,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = response.text
            
            # Log login response details
            self.logger.info(f"RESPONSE STATUS: {response.status_code}")
            self.logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
            self.logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
            self.logger.info(f"RESPONSE TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
            if response.status_code == 200:
                self.auth_token = response_data.get("access_token") if isinstance(response_data, dict) else None
                print(f"✅ Login successful - Token: {self.auth_token[:20] if self.auth_token else 'None'}...")
                return True
            else:
                print(f"❌ Login failed - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time if 'start_time' in locals() else 0
            
            # Log login error details
            self.logger.error(f"LOGIN ERROR: {str(e)}")
            self.logger.error(f"ERROR TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
            print(f"❌ Login error: {e}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    expected_status: int = 200, use_auth: bool = True) -> TestResult:
        """Make HTTP request and return test result"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if use_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if data:
            headers["Content-Type"] = "application/json"
        
        # Log API request details
        self.logger.info("=" * 80)
        self.logger.info(f"API REQUEST: {method} {endpoint}")
        self.logger.info(f"FULL URL: {url}")
        self.logger.info(f"REQUEST HEADERS: {json.dumps(headers, indent=2)}")
        if data:
            self.logger.info(f"REQUEST BODY: {json.dumps(data, indent=2)}")
        else:
            self.logger.info("REQUEST BODY: None")
        self.logger.info("-" * 80)
        
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
            
            # Log API response details
            self.logger.info(f"RESPONSE STATUS: {response.status_code}")
            self.logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
            self.logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
            self.logger.info(f"RESPONSE TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
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
            
            # Log error details
            self.logger.error(f"REQUEST ERROR: {str(e)}")
            self.logger.error(f"ERROR TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
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
        """Run all unified influencer profile API tests"""
        print("🚀 Starting Unified Influencer Profile API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Main functionality tests
        self._run_test_1_get_unified_profile_by_influencer_id()
        self._run_test_2_get_unified_profile_by_user_id()
        self._run_test_3_get_all_unified_profiles()
        self._run_test_4_get_all_unified_profiles_custom_pagination()
        self._run_test_5_get_all_unified_profiles_large_limit()
        
        return self.test_results
    
    def _run_test_1_get_unified_profile_by_influencer_id(self):
        """Test 1: Get Unified Influencer Profile by Influencer ID"""
        print("\n1️⃣ Getting Unified Profile by Influencer ID...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/unified-influencer-profile/{random_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_get_unified_profile_by_user_id(self):
        """Test 2: Get Unified Influencer Profile by User ID"""
        print("\n2️⃣ Getting Unified Profile by User ID...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/unified-influencer-profile/user/{random_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_get_all_unified_profiles(self):
        """Test 3: Get All Unified Influencer Profiles (Default Pagination)"""
        print("\n3️⃣ Getting All Unified Profiles (Default Pagination)...")
        result = self.make_request("GET", "/unified-influencer-profile/?limit=10&offset=0")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_get_all_unified_profiles_custom_pagination(self):
        """Test 4: Get All Unified Influencer Profiles with Custom Pagination"""
        print("\n4️⃣ Getting All Unified Profiles (Custom Pagination)...")
        limit = self.fake.random_int(min=1, max=20)
        offset = self.fake.random_int(min=0, max=50)
        result = self.make_request("GET", f"/unified-influencer-profile/?limit={limit}&offset={offset}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_5_get_all_unified_profiles_large_limit(self):
        """Test 5: Get All Unified Influencer Profiles with Large Limit"""
        print("\n5️⃣ Getting All Unified Profiles (Large Limit)...")
        result = self.make_request("GET", "/unified-influencer-profile/?limit=20&offset=0")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Get Non-existent Influencer Profile
        print("\n❌ Getting Non-existent Influencer Profile...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("GET", f"/unified-influencer-profile/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Get Non-existent User Profile
        print("\n❌ Getting Non-existent User Profile...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("GET", f"/unified-influencer-profile/user/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Invalid Influencer ID Format
        print("\n❌ Getting Profile with Invalid Influencer ID Format...")
        result = self.make_request("GET", "/unified-influencer-profile/invalid_id", expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 4: Invalid User ID Format
        print("\n❌ Getting Profile with Invalid User ID Format...")
        result = self.make_request("GET", "/unified-influencer-profile/user/invalid_id", expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 5: Invalid Pagination Parameters
        print("\n❌ Getting Profiles with Invalid Pagination...")
        result = self.make_request("GET", "/unified-influencer-profile/?limit=-1&offset=-1", expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 6: Large Pagination Values
        print("\n❌ Getting Profiles with Large Pagination Values...")
        result = self.make_request("GET", "/unified-influencer-profile/?limit=1000&offset=1000")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        return self.test_results
    
    def run_authentication_tests(self) -> List[TestResult]:
        """Run authentication error tests"""
        print("\n" + "=" * 60)
        print("🔒 Running Authentication Tests...")
        print("=" * 60)
        
        # Auth Test 1: Get Profile without Authentication
        print("\n🔒 Getting Profile without Authentication...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/unified-influencer-profile/{random_id}", use_auth=False, expected_status=401)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Auth Test 2: Get Profile by User ID without Authentication
        print("\n🔒 Getting Profile by User ID without Authentication...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/unified-influencer-profile/user/{random_id}", use_auth=False, expected_status=401)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Auth Test 3: Get All Profiles without Authentication
        print("\n🔒 Getting All Profiles without Authentication...")
        result = self.make_request("GET", "/unified-influencer-profile/", use_auth=False, expected_status=401)
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
    # Default URL (change this line to modify default URL)
    DEFAULT_BASE_URL = "http://localhost:8000"
    
    # Parse command line arguments
    base_url = DEFAULT_BASE_URL
    test_number = None
    custom_url = None
    
    # Check for custom URL and test number in arguments
    for arg in sys.argv[1:]:
        if arg.startswith("http"):
            custom_url = arg
        elif arg.isdigit():
            test_number = arg
    
    # Use custom URL if provided
    if custom_url:
        base_url = custom_url
        print(f"🔧 Using custom URL from command line: {base_url}")
    else:
        print(f"📍 Using default URL: {base_url}")
    
    # Show usage only if 'help' or '--help' is provided
    if len(sys.argv) > 1 and sys.argv[1] in ['help', '--help', '-h']:
        print("Usage:")
        print("  python run_unified_influencer_profile_tests.py [test_number]")
        print("  python run_unified_influencer_profile_tests.py [base_url] [test_number]")
        print("  python run_unified_influencer_profile_tests.py                    # Run all tests")
        print("  python run_unified_influencer_profile_tests.py 1                  # Run only test 1")
        print("  python run_unified_influencer_profile_tests.py http://localhost:8000 1  # Run test 1 with custom URL")
        print("\nAvailable test numbers:")
        print("  1  - Get Unified Profile by Influencer ID")
        print("  2  - Get Unified Profile by User ID")
        print("  3  - Get All Unified Profiles (Default Pagination)")
        print("  4  - Get All Unified Profiles (Custom Pagination)")
        print("  5  - Get All Unified Profiles (Large Limit)")
        print(f"\nDefault URL: {DEFAULT_BASE_URL}")
        print("To change default URL, modify DEFAULT_BASE_URL in the script")
        sys.exit(0)
    
    tester = UnifiedInfluencerProfileAPITester(base_url)
    
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
            "1": tester._run_test_1_get_unified_profile_by_influencer_id,
            "2": tester._run_test_2_get_unified_profile_by_user_id,
            "3": tester._run_test_3_get_all_unified_profiles,
            "4": tester._run_test_4_get_all_unified_profiles_custom_pagination,
            "5": tester._run_test_5_get_all_unified_profiles_large_limit,
        }
        
        if test_number in test_methods:
            test_methods[test_number]()
        else:
            print(f"❌ Invalid test number: {test_number}")
            print("Available test numbers: 1, 2, 3, 4, 5")
            sys.exit(1)
    else:
        # Run all tests
        tester.run_all_tests()
        # Run error tests
        tester.run_error_tests()
        # Run authentication tests
        tester.run_authentication_tests()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()
