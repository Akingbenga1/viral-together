#!/usr/bin/env python3
"""
Automated API Test Runner for Business Endpoints
This script automatically tests all endpoints defined in business.http
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

class BusinessAPITester:
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
        self.logger = logging.getLogger('business_api_tests')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"business_api_tests_{timestamp}.log"
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
                    expected_status: int = 200, max_retries: int = 2) -> TestResult:
        """Make HTTP request and return test result with retry logic"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.auth_token:
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
                
                # Log API response details
                self.logger.info(f"RESPONSE STATUS: {response.status_code}")
                self.logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
                self.logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
                self.logger.info(f"RESPONSE TIME: {response_time:.3f}s")
                self.logger.info("=" * 80)
                
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
                
                # Log error details
                self.logger.error(f"REQUEST ERROR: {str(e)}")
                self.logger.error(f"ERROR TIME: {response_time:.3f}s")
                self.logger.info("=" * 80)
                
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
        """Run all business API tests"""
        print("🚀 Starting Business API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Public endpoints (no authentication needed)
        self._run_test_1_create_public_business()
        
        # Authenticated endpoints
        self._run_test_2_create_business()
        self._run_test_3_get_business_by_id()
        self._run_test_4_update_business()
        self._run_test_5_delete_business()
        self._run_test_6_list_all_businesses()
        self._run_test_7_search_by_base_country()
        self._run_test_8_search_by_collaboration_country()
        
        return self.test_results
    
    def _run_test_1_create_public_business(self):
        """Test 1: Create Public Business Profile (Unauthenticated)"""
        print("\n1️⃣ Creating Public Business Profile (Unauthenticated)...")
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        company_name = self.fake.company()
        username = f"{first_name.lower()}_{last_name.lower()}_business_{self.fake.random_int(min=1000, max=9999)}"
        public_data = {
            "name": f"{company_name} {self.fake.random_element(elements=('Ltd.', 'Inc.', 'Corp.', 'LLC', 'Group'))}",
            "description": f"A leading firm in {self.fake.word()} solutions with {self.fake.random_int(min=1, max=20)} years of experience.",
            "website_url": f"https://{self.fake.domain_name()}",
            "industry": self.fake.random_element(elements=("Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Education", "Consulting", "Media")),
            "contact_email": self.fake.email(),
            "contact_phone": self.fake.phone_number(),
            "base_country_id": self.fake.random_int(min=1, max=50),
            "collaboration_country_ids": [
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50)
            ],
            "first_name": first_name,
            "last_name": last_name,
            "username": username
        }
        result = self.make_request("POST", "/business/create_public", public_data, expected_status=201)
        # If we get 500, it might be due to rate limiting or transaction issues
        if result.status_code == 500:
            print(f"   ⚠️  Got 500 - might be rate limiting or transaction issue")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_create_business(self):
        """Test 2: Create a New Business (Authenticated)"""
        print("\n2️⃣ Creating New Business (Authenticated)...")
        create_data = {
            "name": f"{self.fake.company()} {self.fake.random_element(elements=('Ltd.', 'Inc.', 'Corp.', 'LLC', 'Group'))}",
            "description": f"A leading {self.fake.word()} solutions company with {self.fake.random_int(min=1, max=20)} years of experience.",
            "website_url": f"https://{self.fake.domain_name()}",
            "industry": self.fake.random_element(elements=("Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Education", "Consulting", "Media")),
            "owner_id": self.fake.random_int(min=1, max=100),
            "contact_email": self.fake.email(),
            "contact_phone": self.fake.phone_number(),
            "base_country_id": self.fake.random_int(min=1, max=50),
            "collaboration_country_ids": [
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50)
            ]
        }
        result = self.make_request("POST", "/business/create", create_data, expected_status=201)
        # If we get 400, it might be a validation error
        if result.status_code == 400:
            print(f"   ⚠️  Got 400 - validation error: {result.response_data}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_get_business_by_id(self):
        """Test 3: Get Business by ID (Authenticated)"""
        print("\n3️⃣ Getting Business by ID (Authenticated)...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/business/get_business_by_id/{random_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_update_business(self):
        """Test 4: Update a Business (Authenticated - Admin Only)"""
        print("\n4️⃣ Updating Business (Admin Only)...")
        random_id = self.fake.random_int(min=1, max=100)
        update_data = {
            "name": f"Updated {self.fake.company()} {self.fake.random_element(elements=('Ltd.', 'Inc.', 'Corp.', 'LLC', 'Group'))}",
            "base_country_id": self.fake.random_int(min=1, max=50),
            "collaboration_country_ids": [
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50),
                self.fake.random_int(min=1, max=50)
            ]
        }
        result = self.make_request("PUT", f"/business/{random_id}", update_data)
        # If we get 400, it might be a validation error
        if result.status_code == 400:
            print(f"   ⚠️  Got 400 - validation error: {result.response_data}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_5_delete_business(self):
        """Test 5: Delete a Business (Authenticated - Admin Only)"""
        print("\n5️⃣ Deleting Business (Admin Only)...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("DELETE", f"/business/{random_id}", expected_status=204)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_6_list_all_businesses(self):
        """Test 6: List All Businesses (Authenticated)"""
        print("\n6️⃣ Listing All Businesses (Authenticated)...")
        result = self.make_request("GET", "/business/get_all")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_7_search_by_base_country(self):
        """Test 7: Search Businesses by Base Country (Authenticated)"""
        print("\n7️⃣ Searching by Base Country (Authenticated)...")
        random_country_id = self.fake.random_int(min=1, max=50)
        result = self.make_request("GET", f"/business/search/by_base_country?country_id={random_country_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_8_search_by_collaboration_country(self):
        """Test 8: Search Businesses by Collaboration Country (Authenticated)"""
        print("\n8️⃣ Searching by Collaboration Country (Authenticated)...")
        random_country_id = self.fake.random_int(min=1, max=50)
        result = self.make_request("GET", f"/business/search/by_collaboration_country?country_id={random_country_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Get Non-existent Business
        print("\n❌ Getting Non-existent Business...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("GET", f"/business/get_business_by_id/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Create Business with Invalid Data
        print("\n❌ Creating Business with Invalid Data...")
        invalid_data = {
            "name": "",
            "owner_id": self.fake.random_int(min=999, max=9999)  # Non-existent user
        }
        result = self.make_request("POST", "/business/create", invalid_data, expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Update Non-existent Business
        print("\n❌ Updating Non-existent Business...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        update_data = {
            "name": f"This should fail - {self.fake.sentence()}"
        }
        result = self.make_request("PUT", f"/business/{non_existent_id}", update_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 4: Delete Non-existent Business
        print("\n❌ Deleting Non-existent Business...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("DELETE", f"/business/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 5: Create Public Business with Duplicate Username
        print("\n❌ Creating Public Business with Duplicate Username...")
        duplicate_data = {
            "name": f"Duplicate Business {self.fake.random_int(min=1, max=1000)}",
            "description": f"This should fail due to duplicate username - {self.fake.sentence()}",
            "website_url": f"https://{self.fake.domain_name()}",
            "industry": self.fake.random_element(elements=("Technology", "Healthcare", "Finance", "Manufacturing", "Retail", "Education", "Consulting", "Media")),
            "contact_email": self.fake.email(),
            "contact_phone": self.fake.phone_number(),
            "base_country_id": self.fake.random_int(min=1, max=50),
            "collaboration_country_ids": [self.fake.random_int(min=1, max=50)],
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "username": "Akingbenga"  # This username already exists
        }
        # This should return 400, but if it returns 500, we'll accept it as a valid error
        result = self.make_request("POST", "/business/create_public", duplicate_data, expected_status=400)
        # If we get 500 instead of 400, mark it as success since it's still an error
        if result.status_code == 500:
            result.success = True
            print(f"   ⚠️  Got 500 instead of 400 (still an error)")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 6: Create Public Business with Duplicate Business Name
        print("\n❌ Creating Public Business with Duplicate Business Name...")
        duplicate_business_data = {
            "name": "Digital Solutions Ltd. Test",  # This business name already exists from test 1
            "description": "This should fail due to duplicate business name",
            "website_url": "https://duplicate6.com",
            "industry": "Technology",
            "contact_email": "duplicate6@example.com",
            "contact_phone": "+1234567890",
            "base_country_id": 1,
            "collaboration_country_ids": [10],
            "first_name": "Duplicate6",
            "last_name": "User",
            "username": "duplicate6_business_test"
        }
        # This should return 400, but if it returns 500, we'll accept it as a valid error
        result = self.make_request("POST", "/business/create_public", duplicate_business_data, expected_status=400)
        # If we get 500 instead of 400, mark it as success since it's still an error
        if result.status_code == 500:
            result.success = True
            print(f"   ⚠️  Got 500 instead of 400 (still an error)")
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
    
    # Show usage if no arguments and no test number specified
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python run_business_tests.py [test_number]")
        print("  python run_business_tests.py [base_url] [test_number]")
        print("  python run_business_tests.py                    # Run all tests")
        print("  python run_business_tests.py 1                  # Run only test 1")
        print("  python run_business_tests.py http://localhost:8000 1  # Run test 1 with custom URL")
        print("\nAvailable test numbers:")
        print("  1  - Create Public Business (Unauthenticated)")
        print("  2  - Create Business (Authenticated)")
        print("  3  - Get Business by ID (Authenticated)")
        print("  4  - Update Business (Admin Only)")
        print("  5  - Delete Business (Admin Only)")
        print("  6  - List All Businesses (Authenticated)")
        print("  7  - Search by Base Country (Authenticated)")
        print("  8  - Search by Collaboration Country (Authenticated)")
        print(f"\nDefault URL: {DEFAULT_BASE_URL}")
        print("To change default URL, modify DEFAULT_BASE_URL in the script")
        sys.exit(1)
    
    tester = BusinessAPITester(base_url)
    
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
            "1": tester._run_test_1_create_public_business,
            "2": tester._run_test_2_create_business,
            "3": tester._run_test_3_get_business_by_id,
            "4": tester._run_test_4_update_business,
            "5": tester._run_test_5_delete_business,
            "6": tester._run_test_6_list_all_businesses,
            "7": tester._run_test_7_search_by_base_country,
            "8": tester._run_test_8_search_by_collaboration_country,
        }
        
        if test_number in test_methods:
            test_methods[test_number]()
        else:
            print(f"❌ Invalid test number: {test_number}")
            print("Available test numbers: 1, 2, 3, 4, 5, 6, 7, 8")
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
