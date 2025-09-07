#!/usr/bin/env python3
"""
Core Location Operations Test Runner
Tests the basic location functionality including geocoding and search endpoints
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import logging
from faker import Faker

# Configure logging
import os
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
os.makedirs(log_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"core_location_api_tests_{timestamp}.log"
log_path = os.path.join(log_dir, log_filename)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
print(f"📝 Logging to file: {log_path}")

class CoreLocationTestRunner:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        })
        
        # Initialize Faker for generating random data
        self.fake = Faker()
        
    def test_geocode_address(self, address: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        """Test geocoding an address to coordinates"""
        url = f"{self.base_url}/api/v1/geocode"
        payload = {"address": address}
        if country_code:
            payload["country_code"] = country_code
            
        # Log API request details
        logger.info("=" * 80)
        logger.info("API REQUEST: POST /api/v1/geocode")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info(f"REQUEST BODY: {json.dumps(payload, indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.post(url, json=payload)
        response_time = time.time() - start_time
        
        # Try to parse JSON response
        try:
            response_data = response.json() if response.content else None
        except json.JSONDecodeError:
            response_data = response.text
        
        # Log API response details
        logger.info(f"RESPONSE STATUS: {response.status_code}")
        logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
        logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
        logger.info(f"RESPONSE TIME: {response_time:.3f}s")
        logger.info("=" * 80)
        
        if response.status_code == 200:
            result = response_data
            logger.info(f"✅ Geocoding successful: {result}")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Geocoding failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Test reverse geocoding coordinates to address"""
        url = f"{self.base_url}/api/v1/reverse-geocode"
        payload = {"latitude": latitude, "longitude": longitude}
        
        # Log API request details
        logger.info("=" * 80)
        logger.info("API REQUEST: POST /api/v1/reverse-geocode")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info(f"REQUEST BODY: {json.dumps(payload, indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.post(url, json=payload)
        response_time = time.time() - start_time
        
        # Try to parse JSON response
        try:
            response_data = response.json() if response.content else None
        except json.JSONDecodeError:
            response_data = response.text
        
        # Log API response details
        logger.info(f"RESPONSE STATUS: {response.status_code}")
        logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
        logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
        logger.info(f"RESPONSE TIME: {response_time:.3f}s")
        logger.info("=" * 80)
        
        if response.status_code == 200:
            result = response_data
            logger.info(f"✅ Reverse geocoding successful: {result}")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Reverse geocoding failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_search_locations(self, query: str, country_code: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Test location search functionality"""
        url = f"{self.base_url}/api/v1/search"
        params = {"query": query, "limit": limit}
        if country_code:
            params["country_code"] = country_code
            
        # Log API request details
        logger.info("=" * 80)
        logger.info("API REQUEST: GET /api/v1/search")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info(f"REQUEST PARAMS: {json.dumps(params, indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.get(url, params=params)
        response_time = time.time() - start_time
        
        # Try to parse JSON response
        try:
            response_data = response.json() if response.content else None
        except json.JSONDecodeError:
            response_data = response.text
        
        # Log API response details
        logger.info(f"RESPONSE STATUS: {response.status_code}")
        logger.info(f"RESPONSE HEADERS: {dict(response.headers)}")
        logger.info(f"RESPONSE BODY: {json.dumps(response_data, indent=2) if isinstance(response_data, (dict, list)) else str(response_data)}")
        logger.info(f"RESPONSE TIME: {response_time:.3f}s")
        logger.info("=" * 80)
        
        if response.status_code == 200:
            result = response_data
            logger.info(f"✅ Location search successful: {len(result) if isinstance(result, list) else 'N/A'} results")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Location search failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all core location operation tests"""
        logger.info("🚀 Starting Core Location Operations Tests")
        
        test_results = {
            "geocoding_tests": [],
            "reverse_geocoding_tests": [],
            "search_tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
        
        # Test geocoding - using Faker for dynamic addresses
        address1 = f"{self.fake.building_number()} {self.fake.street_name()}, {self.fake.city()}, {self.fake.state_abbr()}"
        result = self.test_geocode_address(address1, self.fake.country_code())
        test_results["geocoding_tests"].append(result)
        
        address2 = f"{self.fake.building_number()} {self.fake.street_name()}, {self.fake.city()}"
        result = self.test_geocode_address(address2, self.fake.country_code())
        test_results["geocoding_tests"].append(result)
        
        # Test reverse geocoding - using Faker for dynamic coordinates
        lat1 = round(self.fake.latitude(), 4)
        lon1 = round(self.fake.longitude(), 4)
        result = self.test_reverse_geocode(lat1, lon1)
        test_results["reverse_geocoding_tests"].append(result)
        
        lat2 = round(self.fake.latitude(), 4)
        lon2 = round(self.fake.longitude(), 4)
        result = self.test_reverse_geocode(lat2, lon2)
        test_results["reverse_geocoding_tests"].append(result)
        
        # Test location search - using Faker for dynamic search terms
        search_city1 = self.fake.city()
        result = self.test_search_locations(search_city1, limit=self.fake.random_int(min=5, max=20))
        test_results["search_tests"].append(result)
        
        search_city2 = self.fake.city()
        result = self.test_search_locations(search_city2, self.fake.country_code(), self.fake.random_int(min=3, max=15))
        test_results["search_tests"].append(result)
        
        # Calculate summary
        all_tests = (test_results["geocoding_tests"] + 
                    test_results["reverse_geocoding_tests"] + 
                    test_results["search_tests"])
        
        test_results["summary"]["total"] = len(all_tests)
        test_results["summary"]["passed"] = sum(1 for test in all_tests if test.get("success", False))
        test_results["summary"]["failed"] = test_results["summary"]["total"] - test_results["summary"]["passed"]
        
        logger.info(f"📊 Test Summary: {test_results['summary']['passed']}/{test_results['summary']['total']} tests passed")
        
        return test_results

def main():
    """Main function to run the tests"""
    # Default URL (change this line to modify default URL)
    DEFAULT_BASE_URL = "http://localhost:8000"
    AUTH_TOKEN = "your_auth_token_here"
    
    # Parse command line arguments for custom URL
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
    
    if AUTH_TOKEN == "your_auth_token_here":
        logger.error("❌ Please update AUTH_TOKEN with your actual authentication token")
        return
    
    try:
        runner = CoreLocationTestRunner(base_url, AUTH_TOKEN)
        results = runner.run_all_tests()
        
        print(f"\n📊 SUMMARY: {results['summary']['passed']}/{results['summary']['total']} tests passed")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"core_location_test_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Test runner failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
