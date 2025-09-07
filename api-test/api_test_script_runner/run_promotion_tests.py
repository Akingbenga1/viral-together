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

class PromotionAPITester:
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
        self.logger = logging.getLogger('promotion_api_tests')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"promotion_api_tests_{timestamp}.log"
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
        promotion_names = ["Summer Sale", "Black Friday", "Holiday Special", "Flash Sale", "Weekend Deal", "New Year Promotion", "Spring Collection", "Tech Tuesday"]
        promotion_items = ["Electronics", "Fashion", "Home Decor", "Beauty Products", "Sports Equipment", "Books", "Gadgets", "Accessories"]
        target_audiences = ["Young Adults", "Families", "Professionals", "Students", "Seniors", "Tech Enthusiasts", "Fashion Lovers", "Fitness Enthusiasts"]
        
        start_date = self.fake.date_between(start_date='-30d', end_date='+30d')
        end_date = self.fake.date_between(start_date=start_date, end_date='+60d')
        
        create_data = {
            "business_id": self.fake.random_int(min=1, max=100),
            "promotion_name": f"{self.fake.random_element(elements=promotion_names)} {self.fake.random_int(min=1, max=1000)}",
            "promotion_item": self.fake.random_element(elements=promotion_items),
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "discount": round(self.fake.random.uniform(5, 50), 1),
            "budget": round(self.fake.random.uniform(1000, 10000), 2),
            "target_audience": self.fake.random_element(elements=target_audiences),
            "social_media_platform_id": self.fake.random_int(min=1, max=20)
        }
        result = self.make_request("POST", "/promotions/", create_data, expected_status=200)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_get_promotion(self):
        """Test 2: Get Promotion by ID"""
        print("\n2️⃣ Getting Promotion by ID...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/promotions/{random_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_update_promotion(self):
        """Test 3: Update a Promotion"""
        print("\n3️⃣ Updating Promotion...")
        random_id = self.fake.random_int(min=1, max=100)
        promotion_names = ["Summer Sale", "Black Friday", "Holiday Special", "Flash Sale", "Weekend Deal", "New Year Promotion", "Spring Collection", "Tech Tuesday"]
        promotion_items = ["Electronics", "Fashion", "Home Decor", "Beauty Products", "Sports Equipment", "Books", "Gadgets", "Accessories"]
        target_audiences = ["Young Adults", "Families", "Professionals", "Students", "Seniors", "Tech Enthusiasts", "Fashion Lovers", "Fitness Enthusiasts"]
        
        start_date = self.fake.date_between(start_date='-30d', end_date='+30d')
        end_date = self.fake.date_between(start_date=start_date, end_date='+60d')
        
        update_data = {
            "business_id": self.fake.random_int(min=1, max=100),
            "promotion_name": f"Updated {self.fake.random_element(elements=promotion_names)} {self.fake.random_int(min=1, max=1000)}",
            "promotion_item": self.fake.random_element(elements=promotion_items),
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "discount": round(self.fake.random.uniform(5, 50), 1),
            "budget": round(self.fake.random.uniform(1000, 10000), 2),
            "target_audience": self.fake.random_element(elements=target_audiences),
            "social_media_platform_id": self.fake.random_int(min=1, max=20)
        }
        result = self.make_request("PUT", f"/promotions/{random_id}", update_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_delete_promotion(self):
        """Test 4: Delete a Promotion"""
        print("\n4️⃣ Deleting Promotion...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("DELETE", f"/promotions/{random_id}", expected_status=200)
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
        collaboration_types = ["sponsored_post", "product_review", "brand_ambassador", "giveaway", "story_takeover", "live_stream", "unboxing", "tutorial"]
        deliverables_options = ["6 Instagram posts every day.1 article post per week", "Honest review video on TikTok", "3 Instagram stories per day", "1 YouTube video per week", "Daily Twitter posts", "Facebook live session", "LinkedIn article", "Pinterest board creation"]
        messages = ["Ready to create viral magic together! My engaged audience would be thrilled about this collaboration!", "This product aligns perfectly with my audience!", "I'm excited to work with your brand!", "My followers would love this!", "Perfect match for my content style!", "Looking forward to this partnership!", "This collaboration will be amazing!", "Can't wait to showcase your product!"]
        
        random_promotion_id = self.fake.random_int(min=1, max=100)
        interest_data = {
            "influencer_id": self.fake.random_int(min=1, max=100),
            "proposed_amount": round(self.fake.random.uniform(500, 5000), 2),
            "collaboration_type": self.fake.random_element(elements=collaboration_types),
            "deliverables": self.fake.random_element(elements=deliverables_options),
            "message": self.fake.random_element(elements=messages)
        }
        result = self.make_request("POST", f"/promotions/{random_promotion_id}/show-interest", interest_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_7_show_interest_no_amount(self):
        """Test 7: Show Interest without Proposed Amount"""
        print("\n7️⃣ Showing Interest (No Amount)...")
        collaboration_types = ["sponsored_post", "product_review", "brand_ambassador", "giveaway", "story_takeover", "live_stream", "unboxing", "tutorial"]
        deliverables_options = ["6 Instagram posts every day.1 article post per week", "Honest review video on TikTok", "3 Instagram stories per day", "1 YouTube video per week", "Daily Twitter posts", "Facebook live session", "LinkedIn article", "Pinterest board creation"]
        messages = ["Ready to create viral magic together! My engaged audience would be thrilled about this collaboration!", "This product aligns perfectly with my audience!", "I'm excited to work with your brand!", "My followers would love this!", "Perfect match for my content style!", "Looking forward to this partnership!", "This collaboration will be amazing!", "Can't wait to showcase your product!"]
        
        random_promotion_id = self.fake.random_int(min=1, max=100)
        interest_data = {
            "influencer_id": self.fake.random_int(min=1, max=100),
            "collaboration_type": self.fake.random_element(elements=collaboration_types),
            "deliverables": self.fake.random_element(elements=deliverables_options),
            "message": self.fake.random_element(elements=messages)
        }
        result = self.make_request("POST", f"/promotions/{random_promotion_id}/show-interest", interest_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_8_show_interest_minimal(self):
        """Test 8: Show Interest with Minimal Data"""
        print("\n8️⃣ Showing Interest (Minimal Data)...")
        collaboration_types = ["sponsored_post", "product_review", "brand_ambassador", "giveaway", "story_takeover", "live_stream", "unboxing", "tutorial"]
        
        random_promotion_id = self.fake.random_int(min=1, max=100)
        interest_data = {
            "influencer_id": self.fake.random_int(min=1, max=100),
            "collaboration_type": self.fake.random_element(elements=collaboration_types)
        }
        result = self.make_request("POST", f"/promotions/{random_promotion_id}/show-interest", interest_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_show_interest_custom_type(self):
        """Test 9: Show Interest with Custom Collaboration Type"""
        print("\n9️⃣ Showing Interest (Custom Type)...")
        custom_collaboration_types = ["event_coverage", "product_launch", "seasonal_campaign", "charity_partnership", "educational_content", "behind_scenes", "exclusive_access", "community_building"]
        deliverables_options = ["Live event coverage, 3 posts, highlight reel", "Product launch announcement, 5 posts", "Seasonal campaign content, 10 posts", "Charity partnership announcement", "Educational tutorial series", "Behind the scenes content", "Exclusive access content", "Community building activities"]
        messages = ["I have experience covering similar events and can provide great exposure!", "Perfect timing for this product launch!", "This seasonal campaign aligns with my content!", "I'm passionate about this charity cause!", "I love creating educational content!", "My audience loves behind the scenes content!", "I can provide exclusive access to my followers!", "I'm great at building communities!"]
        
        random_promotion_id = self.fake.random_int(min=1, max=100)
        interest_data = {
            "influencer_id": self.fake.random_int(min=1, max=100),
            "proposed_amount": round(self.fake.random.uniform(500, 3000), 2),
            "collaboration_type": self.fake.random_element(elements=custom_collaboration_types),
            "deliverables": self.fake.random_element(elements=deliverables_options),
            "message": self.fake.random_element(elements=messages)
        }
        result = self.make_request("POST", f"/promotions/{random_promotion_id}/show-interest", interest_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Try to Show Interest Twice (Should Fail - Duplicate)
        print("\n❌ Trying to Show Interest Twice (Duplicate)...")
        collaboration_types = ["sponsored_post", "product_review", "brand_ambassador", "giveaway", "story_takeover", "live_stream", "unboxing", "tutorial"]
        interest_data = {
            "influencer_id": self.fake.random_int(min=1, max=100),
            "collaboration_type": self.fake.random_element(elements=collaboration_types),
            "message": f"Trying to submit interest again - {self.fake.sentence()}"
        }
        random_promotion_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("POST", f"/promotions/{random_promotion_id}/show-interest", interest_data, expected_status=400)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Show Interest in Non-existent Promotion (Should Fail - 404)
        print("\n❌ Showing Interest in Non-existent Promotion...")
        collaboration_types = ["sponsored_post", "product_review", "brand_ambassador", "giveaway", "story_takeover", "live_stream", "unboxing", "tutorial"]
        interest_data = {
            "influencer_id": self.fake.random_int(min=1, max=100),
            "collaboration_type": self.fake.random_element(elements=collaboration_types)
        }
        non_existent_promotion_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("POST", f"/promotions/{non_existent_promotion_id}/show-interest", interest_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Show Interest with Non-existent Influencer (Should Fail - 404)
        print("\n❌ Showing Interest with Non-existent Influencer...")
        collaboration_types = ["sponsored_post", "product_review", "brand_ambassador", "giveaway", "story_takeover", "live_stream", "unboxing", "tutorial"]
        interest_data = {
            "influencer_id": self.fake.random_int(min=999, max=9999),
            "collaboration_type": self.fake.random_element(elements=collaboration_types)
        }
        random_promotion_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("POST", f"/promotions/{random_promotion_id}/show-interest", interest_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 4: Get Non-existent Promotion (Should Fail - 404)
        print("\n❌ Getting Non-existent Promotion...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("GET", f"/promotions/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 5: Update Non-existent Promotion (Should Fail - 404)
        print("\n❌ Updating Non-existent Promotion...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        start_date = self.fake.date_between(start_date='-30d', end_date='+30d')
        end_date = self.fake.date_between(start_date=start_date, end_date='+60d')
        update_data = {
            "business_id": self.fake.random_int(min=1, max=100),
            "promotion_name": f"This should fail - {self.fake.sentence()}",
            "promotion_item": self.fake.word(),
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "social_media_platform_id": self.fake.random_int(min=1, max=20)
        }
        result = self.make_request("PUT", f"/promotions/{non_existent_id}", update_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 6: Delete Non-existent Promotion (Should Fail - 404)
        print("\n❌ Deleting Non-existent Promotion...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("DELETE", f"/promotions/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 7: Create Promotion with Invalid Business ID (Should Fail - 404)
        print("\n❌ Creating Promotion with Invalid Business ID...")
        start_date = self.fake.date_between(start_date='-30d', end_date='+30d')
        end_date = self.fake.date_between(start_date=start_date, end_date='+60d')
        create_data = {
            "business_id": self.fake.random_int(min=999, max=9999),
            "promotion_name": f"Invalid Business Test - {self.fake.sentence()}",
            "promotion_item": self.fake.word(),
            "start_date": f"{start_date}T00:00:00",
            "end_date": f"{end_date}T00:00:00",
            "social_media_platform_id": self.fake.random_int(min=1, max=20)
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
        print("  python run_promotion_tests.py [test_number]")
        print("  python run_promotion_tests.py [base_url] [test_number]")
        print("  python run_promotion_tests.py                    # Run all tests")
        print("  python run_promotion_tests.py 1                  # Run only test 1")
        print("  python run_promotion_tests.py http://localhost:8000 1  # Run test 1 with custom URL")
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
        print(f"\nDefault URL: {DEFAULT_BASE_URL}")
        print("To change default URL, modify DEFAULT_BASE_URL in the script")
        sys.exit(1)
    
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
