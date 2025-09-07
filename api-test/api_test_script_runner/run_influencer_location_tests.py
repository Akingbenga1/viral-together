#!/usr/bin/env python3
"""
Influencer Location Management Test Runner
Tests CRUD operations for influencer locations
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
log_filename = f"influencer_location_api_tests_{timestamp}.log"
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

class InfluencerLocationTestRunner:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        })
        self.created_location_ids = []
        
        # Initialize Faker for generating random data
        self.fake = Faker()
        
    def test_add_influencer_location(self, influencer_id: int, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test adding a location for an influencer"""
        url = f"{self.base_url}/api/v1/influencers/{influencer_id}/locations"
        
        # Log API request details
        logger.info("=" * 80)
        logger.info(f"API REQUEST: POST /api/v1/influencers/{influencer_id}/locations")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info(f"REQUEST BODY: {json.dumps(location_data, indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.post(url, json=location_data)
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
            location_id = result.get('id') if isinstance(result, dict) else None
            if location_id:
                self.created_location_ids.append(location_id)
            logger.info(f"✅ Location added successfully: ID {location_id}")
            return {"success": True, "data": result, "status_code": response.status_code, "location_id": location_id}
        else:
            logger.error(f"❌ Failed to add location: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_get_influencer_locations(self, influencer_id: int) -> Dict[str, Any]:
        """Test getting all locations for an influencer"""
        url = f"{self.base_url}/api/v1/influencers/{influencer_id}/locations"
        
        # Log API request details
        logger.info("=" * 80)
        logger.info(f"API REQUEST: GET /api/v1/influencers/{influencer_id}/locations")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.get(url)
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
            logger.info(f"✅ Retrieved {len(result) if isinstance(result, list) else 'N/A'} locations")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Failed to get locations: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_update_influencer_location(self, location_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test updating an influencer location"""
        url = f"{self.base_url}/api/v1/influencers/locations/{location_id}"
        
        # Log API request details
        logger.info("=" * 80)
        logger.info(f"API REQUEST: PUT /api/v1/influencers/locations/{location_id}")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info(f"REQUEST BODY: {json.dumps(update_data, indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.put(url, json=update_data)
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
            logger.info(f"✅ Location updated successfully")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Failed to update location: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_delete_influencer_location(self, location_id: int) -> Dict[str, Any]:
        """Test deleting an influencer location"""
        url = f"{self.base_url}/api/v1/influencers/locations/{location_id}"
        
        # Log API request details
        logger.info("=" * 80)
        logger.info(f"API REQUEST: DELETE /api/v1/influencers/locations/{location_id}")
        logger.info(f"FULL URL: {url}")
        logger.info(f"REQUEST HEADERS: {json.dumps(dict(self.session.headers), indent=2)}")
        logger.info("-" * 80)
        
        start_time = time.time()
        response = self.session.delete(url)
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
            logger.info(f"✅ Location deleted successfully")
            return {"success": True, "data": response_data, "status_code": response.status_code}
        else:
            logger.error(f"❌ Failed to delete location: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all influencer location management tests"""
        logger.info("🚀 Starting Influencer Location Management Tests")
        
        test_results = {
            "add_tests": [],
            "get_tests": [],
            "update_tests": [],
            "delete_tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
        
        # Test data for locations - using Faker for dynamic data
        test_locations = []
        for i in range(2):
            city = self.fake.city()
            state = self.fake.state()
            country = self.fake.country()
            test_locations.append({
                "city_name": city,
                "region_name": state,
                "region_code": self.fake.state_abbr(),
                "country_code": self.fake.country_code(),
                "country_name": country,
                "latitude": round(self.fake.latitude(), 4),
                "longitude": round(self.fake.longitude(), 4),
                "postcode": self.fake.postcode(),
                "time_zone": self.fake.timezone(),
                "is_primary": i == 0  # First location is primary
            })
        
        # Test adding locations
        random_influencer_id = self.fake.random_int(min=1, max=100)
        for i, location_data in enumerate(test_locations):
            result = self.test_add_influencer_location(random_influencer_id, location_data)
            test_results["add_tests"].append(result)
            time.sleep(0.5)  # Small delay between requests
        
        # Test getting locations
        result = self.test_get_influencer_locations(random_influencer_id)
        test_results["get_tests"].append(result)
        
        random_influencer_id_2 = self.fake.random_int(min=1, max=100)
        result = self.test_get_influencer_locations(random_influencer_id_2)
        test_results["get_tests"].append(result)
        
        # Test updating locations (if we have created locations)
        if self.created_location_ids:
            city = self.fake.city()
            country = self.fake.country()
            update_data = {
                "city_name": f"{city} Updated",
                "country_code": self.fake.country_code(),
                "country_name": country,
                "latitude": round(self.fake.latitude(), 4),
                "longitude": round(self.fake.longitude(), 4),
                "is_primary": self.fake.boolean()
            }
            result = self.test_update_influencer_location(self.created_location_ids[0], update_data)
            test_results["update_tests"].append(result)
        
        # Test deleting locations (if we have created locations)
        if len(self.created_location_ids) > 1:
            result = self.test_delete_influencer_location(self.created_location_ids[1])
            test_results["delete_tests"].append(result)
        
        # Calculate summary
        all_tests = (test_results["add_tests"] + test_results["get_tests"] + 
                    test_results["update_tests"] + test_results["delete_tests"])
        
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
        runner = InfluencerLocationTestRunner(base_url, AUTH_TOKEN)
        results = runner.run_all_tests()
        
        print(f"\n📊 SUMMARY: {results['summary']['passed']}/{results['summary']['total']} tests passed")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"influencer_location_test_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Test runner failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
