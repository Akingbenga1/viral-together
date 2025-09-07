#!/usr/bin/env python3
"""
Recommendations API Test Script
Tests all recommendations endpoints including generation, retrieval, updates, and analysis triggers.
"""

import requests
import json
import sys
import time
import getpass
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from faker import Faker

@dataclass
class TestResult:
    test_name: str
    success: bool
    status_code: int
    response_time: float
    error_message: str = ""
    response_data: Dict[str, Any] = None

class RecommendationsAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token = None
        
        # Initialize Faker for generating random data
        self.fake = Faker()
        self.test_results: List[TestResult] = []
        
        # Test data
        self.test_user_id = 1
        self.test_recommendation_id = 1
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('recommendations_api_tests')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"recommendations_api_tests_{timestamp}.log"
        log_path = os.path.join(log_dir, log_filename)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        print(f"📝 Logging to file: {log_path}")
        
    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        try:
            print("🔐 Authenticating...")
            
            # Get database authentication credentials from user
            username = input("Enter database authentication username: ")
            password = getpass.getpass("Enter database authentication password: ")
            
            url = f"{self.base_url}/auth/token"
            auth_data = {
                "username": username,
                "password": password
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            # Log authentication request details
            self.logger.info("=" * 80)
            self.logger.info("API REQUEST: POST /auth/token (AUTHENTICATION)")
            self.logger.info(f"FULL URL: {url}")
            self.logger.info(f"REQUEST HEADERS: {json.dumps(headers, indent=2)}")
            self.logger.info(f"REQUEST BODY: username={username}&password=***HIDDEN***")
            self.logger.info("-" * 80)
            
            start_time = time.time()
            
            response = self.session.post(
                url,
                data=auth_data,
                headers=headers
            )
            
            response_time = time.time() - start_time
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = response.text
            
            # Log authentication response details
            self.logger.info(f"RESPONSE STATUS: {response.status_code}")
            self.logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
            self.logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
            self.logger.info(f"RESPONSE TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
            if response.status_code == 200:
                token_data = response_data if isinstance(response_data, dict) else {}
                self.access_token = token_data.get("access_token")
                if self.access_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    print("✅ Authentication successful")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            response_time = time.time() - start_time if 'start_time' in locals() else 0
            
            # Log authentication error details
            self.logger.error(f"AUTHENTICATION ERROR: {str(e)}")
            self.logger.error(f"ERROR TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> TestResult:
        """Make HTTP request and return test result"""
        url = f"{self.base_url}{endpoint}"
        
        # Log API request details
        self.logger.info("=" * 80)
        self.logger.info(f"API REQUEST: {method} {endpoint}")
        self.logger.info(f"FULL URL: {url}")
        self.logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        if data:
            self.logger.info(f"REQUEST BODY: {json.dumps(data, indent=2)}")
        else:
            self.logger.info("REQUEST BODY: None")
        self.logger.info("-" * 80)
        
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                # Log error for unsupported method
                self.logger.error(f"UNSUPPORTED METHOD: {method}")
                self.logger.info("=" * 80)
                return TestResult(
                    test_name=f"{method} {endpoint}",
                    success=False,
                    status_code=0,
                    response_time=0,
                    error_message=f"Unsupported method: {method}"
                )
            
            response_time = time.time() - start_time
            success = response.status_code == expected_status
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
            
            # Log API response details
            self.logger.info(f"RESPONSE STATUS: {response.status_code}")
            self.logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
            self.logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
            self.logger.info(f"RESPONSE TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
            return TestResult(
                test_name=f"{method} {endpoint}",
                success=success,
                status_code=response.status_code,
                response_time=response_time,
                error_message="" if success else f"Expected {expected_status}, got {response.status_code}",
                response_data=response_data
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Log error details
            self.logger.error(f"REQUEST ERROR: {str(e)}")
            self.logger.error(f"ERROR TIME: {response_time:.3f}s")
            self.logger.info("=" * 80)
            
            return TestResult(
                test_name=f"{method} {endpoint}",
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=str(e)
            )
    
    def run_test_1_generate_recommendations(self) -> TestResult:
        """Test: Generate recommendations for user ID 1"""
        random_user_id = self.fake.random_int(min=1, max=100)
        print(f"\n🧪 Test 1: Generate recommendations for user {random_user_id}")
        return self.make_request(
            method="POST",
            endpoint=f"/recommendations/generate/{random_user_id}",
            expected_status=200
        )
    
    def run_test_2_get_user_recommendations(self) -> TestResult:
        """Test: Get all recommendations for user ID 1"""
        random_user_id = self.fake.random_int(min=1, max=100)
        print(f"\n🧪 Test 2: Get all recommendations for user {random_user_id}")
        return self.make_request(
            method="GET",
            endpoint=f"/recommendations/user/{random_user_id}",
            expected_status=200
        )
    
    def run_test_3_get_specific_recommendation(self) -> TestResult:
        """Test: Get specific recommendation by ID"""
        random_recommendation_id = self.fake.random_int(min=1, max=100)
        print(f"\n🧪 Test 3: Get specific recommendation ID {random_recommendation_id}")
        return self.make_request(
            method="GET",
            endpoint=f"/recommendations/{random_recommendation_id}",
            expected_status=200
        )
    
    def run_test_4_update_recommendation(self) -> TestResult:
        """Test: Update recommendation"""
        random_recommendation_id = self.fake.random_int(min=1, max=100)
        print(f"\n🧪 Test 4: Update recommendation ID {random_recommendation_id}")
        statuses = ["implemented", "pending", "in_progress", "completed", "cancelled", "reviewed"]
        user_levels = ["beginner", "intermediate", "advanced", "expert", "professional"]
        update_data = {
            "status": self.fake.random_element(elements=statuses),
            "user_level": self.fake.random_element(elements=user_levels)
        }
        return self.make_request(
            method="PUT",
            endpoint=f"/recommendations/{random_recommendation_id}",
            data=update_data,
            expected_status=200
        )
    
    def run_test_5_delete_recommendation(self) -> TestResult:
        """Test: Delete recommendation"""
        random_recommendation_id = self.fake.random_int(min=1, max=100)
        print(f"\n🧪 Test 5: Delete recommendation ID {random_recommendation_id}")
        return self.make_request(
            method="DELETE",
            endpoint=f"/recommendations/{random_recommendation_id}",
            expected_status=200
        )
    
    def run_test_6_trigger_analysis(self) -> TestResult:
        """Test: Manually trigger analysis for user ID 1"""
        random_user_id = self.fake.random_int(min=1, max=100)
        print(f"\n🧪 Test 6: Trigger analysis for user {random_user_id}")
        return self.make_request(
            method="POST",
            endpoint=f"/recommendations/trigger-analysis/{random_user_id}",
            expected_status=200
        )
    
    def run_test_7_generate_nonexistent_user(self) -> TestResult:
        """Test: Generate recommendations for non-existent user (error case)"""
        non_existent_user_id = self.fake.random_int(min=999, max=9999)
        print(f"\n🧪 Test 7: Generate recommendations for non-existent user {non_existent_user_id}")
        return self.make_request(
            method="POST",
            endpoint=f"/recommendations/generate/{non_existent_user_id}",
            expected_status=404
        )
    
    def run_test_8_get_nonexistent_recommendation(self) -> TestResult:
        """Test: Get non-existent recommendation (error case)"""
        non_existent_recommendation_id = self.fake.random_int(min=999, max=9999)
        print(f"\n🧪 Test 8: Get non-existent recommendation ID {non_existent_recommendation_id}")
        return self.make_request(
            method="GET",
            endpoint=f"/recommendations/{non_existent_recommendation_id}",
            expected_status=404
        )
    
    def run_test_9_update_nonexistent_recommendation(self) -> TestResult:
        """Test: Update non-existent recommendation (error case)"""
        non_existent_recommendation_id = self.fake.random_int(min=999, max=9999)
        print(f"\n🧪 Test 9: Update non-existent recommendation ID {non_existent_recommendation_id}")
        statuses = ["implemented", "pending", "in_progress", "completed", "cancelled", "reviewed"]
        user_levels = ["beginner", "intermediate", "advanced", "expert", "professional"]
        update_data = {
            "status": self.fake.random_element(elements=statuses),
            "user_level": self.fake.random_element(elements=user_levels)
        }
        return self.make_request(
            method="PUT",
            endpoint=f"/recommendations/{non_existent_recommendation_id}",
            data=update_data,
            expected_status=404
        )
    
    def run_test_10_delete_nonexistent_recommendation(self) -> TestResult:
        """Test: Delete non-existent recommendation (error case)"""
        non_existent_recommendation_id = self.fake.random_int(min=999, max=9999)
        print(f"\n🧪 Test 10: Delete non-existent recommendation ID {non_existent_recommendation_id}")
        return self.make_request(
            method="DELETE",
            endpoint=f"/recommendations/{non_existent_recommendation_id}",
            expected_status=404
        )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all recommendation tests"""
        print("🎯 RECOMMENDATIONS API TEST SUITE")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return []
        
        # Run all tests
        tests = [
            ("Generate Recommendations", self.run_test_1_generate_recommendations),
            ("Get User Recommendations", self.run_test_2_get_user_recommendations),
            ("Get Specific Recommendation", self.run_test_3_get_specific_recommendation),
            ("Update Recommendation", self.run_test_4_update_recommendation),
            ("Delete Recommendation", self.run_test_5_delete_recommendation),
            ("Trigger Analysis", self.run_test_6_trigger_analysis),
            ("Generate Non-existent User (Error)", self.run_test_7_generate_nonexistent_user),
            ("Get Non-existent Recommendation (Error)", self.run_test_8_get_nonexistent_recommendation),
            ("Update Non-existent Recommendation (Error)", self.run_test_9_update_nonexistent_recommendation),
            ("Delete Non-existent Recommendation (Error)", self.run_test_10_delete_nonexistent_recommendation)
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.test_results.append(result)
                
                # Print result
                status = "✅ PASSED" if result.success else "❌ FAILED"
                print(f"   {status} - {result.status_code} ({result.response_time:.2f}s)")
                
                if not result.success and result.error_message:
                    print(f"      Error: {result.error_message}")
                
            except Exception as e:
                error_result = TestResult(
                    test_name=test_name,
                    success=False,
                    status_code=0,
                    response_time=0,
                    error_message=str(e)
                )
                self.test_results.append(error_result)
                print(f"   ❌ FAILED - Exception: {str(e)}")
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 RECOMMENDATIONS API TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Calculate total execution time
        total_execution_time = sum(result.response_time for result in self.test_results)
        print(f"\n⏱️  Total Execution Time: {total_execution_time:.2f}s")
        
        # Show failed tests
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.success:
                    print(f"   - {result.test_name}: {result.status_code}")
                    if result.error_message:
                        print(f"     Error: {result.error_message}")
        
        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Overall status
        if failed_tests == 0:
            print("\n🎉 ALL RECOMMENDATIONS TESTS PASSED! 🎉")
        else:
            print(f"\n⚠️  {failed_tests} TEST(S) FAILED")

def main():
    """Main function to run the recommendations API tests"""
    # Default URL (change this line to modify default URL)
    DEFAULT_BASE_URL = "http://localhost:8000"
    
    # Parse command line arguments
    base_url = DEFAULT_BASE_URL
    custom_url = None
    
    # Check for custom URL in arguments
    for arg in sys.argv[1:]:
        if arg.startswith("http"):
            custom_url = arg
    
    # Use custom URL if provided
    if custom_url:
        base_url = custom_url
        print(f"🔧 Using custom URL from command line: {base_url}")
    else:
        print(f"📍 Using default URL: {base_url}")
    
    # Show usage if no arguments provided
    if len(sys.argv) == 1:
        print("🎯 RECOMMENDATIONS API TEST RUNNER")
        print("=" * 50)
        print("Usage: python run_recommendations_tests.py [base_url]")
        print("Example: python run_recommendations_tests.py")
        print("Example: python run_recommendations_tests.py http://localhost:8000")
        print(f"\nDefault URL: {DEFAULT_BASE_URL}")
        print("To change default URL, modify DEFAULT_BASE_URL in the script")
        sys.exit(1)
    
    # Validate base_url format
    if not base_url.startswith(('http://', 'https://')):
        print("❌ Error: Base URL must start with http:// or https://")
        print(f"   Provided: {base_url}")
        sys.exit(1)
    
    # Run tests
    tester = RecommendationsAPITester(base_url)
    results = tester.run_all_tests()
    
    # Print summary
    tester.print_summary()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results if not result.success)
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()
