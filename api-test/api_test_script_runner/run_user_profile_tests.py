#!/usr/bin/env python3
"""
User Profile API Test Script

This script tests the user profile update endpoints:
- GET /user/profile - Get current user profile
- PUT /user/profile/update - Update user profile information
- PUT /user/profile/password - Update user password

Usage:
    python run_user_profile_tests.py

Requirements:
    - Valid access token for authentication
    - API server running on localhost:8000
"""

import requests
import json
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserProfileAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        
    def set_auth_token(self, token: str):
        """Set the authentication token for API requests"""
        self.access_token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Make an API request and return the response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"API REQUEST: {method} {endpoint}")
            if data:
                logger.info(f"REQUEST DATA: {json.dumps(data, indent=2)}")
            
            response = self.session.request(method, url, json=data)
            
            logger.info(f"RESPONSE STATUS: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"RESPONSE DATA: {json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
                logger.info(f"RAW RESPONSE: {response.text}")
            
            if response.status_code != expected_status:
                logger.warning(f"Expected status {expected_status}, got {response.status_code}")
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": response.status_code == expected_status
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
    
    def test_get_profile(self) -> Dict[str, Any]:
        """Test getting current user profile"""
        logger.info("=" * 50)
        logger.info("TEST: Get User Profile")
        logger.info("=" * 50)
        
        return self.make_request("GET", "/user/profile")
    
    def test_update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test updating user profile"""
        logger.info("=" * 50)
        logger.info("TEST: Update User Profile")
        logger.info("=" * 50)
        
        return self.make_request("PUT", "/user/profile/update", profile_data)
    
    def test_update_password(self, password_data: Dict[str, str]) -> Dict[str, Any]:
        """Test updating user password"""
        logger.info("=" * 50)
        logger.info("TEST: Update User Password")
        logger.info("=" * 50)
        
        return self.make_request("PUT", "/user/profile/password", password_data)
    
    def test_validation_errors(self) -> Dict[str, Any]:
        """Test various validation error scenarios"""
        logger.info("=" * 50)
        logger.info("TEST: Validation Errors")
        logger.info("=" * 50)
        
        results = {}
        
        # Test invalid email
        logger.info("Testing invalid email format...")
        results["invalid_email"] = self.make_request(
            "PUT", 
            "/user/profile/update", 
            {"email": "invalid-email-format"},
            expected_status=422
        )
        
        # Test weak password
        logger.info("Testing weak password...")
        results["weak_password"] = self.make_request(
            "PUT",
            "/user/profile/password",
            {
                "current_password": "test123",
                "new_password": "weak",
                "confirm_password": "weak"
            },
            expected_status=422
        )
        
        # Test password mismatch
        logger.info("Testing password mismatch...")
        results["password_mismatch"] = self.make_request(
            "PUT",
            "/user/profile/password",
            {
                "current_password": "test123",
                "new_password": "NewPassword123",
                "confirm_password": "DifferentPassword123"
            },
            expected_status=422
        )
        
        return results
    
    def run_all_tests(self):
        """Run all user profile tests"""
        if not self.access_token:
            logger.error("No access token provided. Please set authentication token first.")
            return
        
        logger.info("Starting User Profile API Tests...")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Access Token: {self.access_token[:20]}...")
        
        # Test 1: Get current profile
        profile_result = self.test_get_profile()
        
        # Test 2: Update profile with valid data
        update_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@example.com",
            "mobile_number": "+1234567890"
        }
        update_result = self.test_update_profile(update_data)
        
        # Test 3: Update password (this will fail with current password, but tests the endpoint)
        password_data = {
            "current_password": "wrong_current_password",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
        password_result = self.test_update_password(password_data)
        
        # Test 4: Validation errors
        validation_results = self.test_validation_errors()
        
        # Summary
        logger.info("=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Get Profile: {'PASS' if profile_result['success'] else 'FAIL'}")
        logger.info(f"Update Profile: {'PASS' if update_result['success'] else 'FAIL'}")
        logger.info(f"Update Password: {'PASS' if password_result['success'] else 'FAIL'}")
        
        validation_passed = all(result['success'] for result in validation_results.values())
        logger.info(f"Validation Tests: {'PASS' if validation_passed else 'FAIL'}")
        
        return {
            "profile_test": profile_result,
            "update_test": update_result,
            "password_test": password_result,
            "validation_tests": validation_results
        }

def main():
    """Main function to run the tests"""
    print("User Profile API Test Script")
    print("=" * 40)
    
    # Get access token from user
    access_token = input("Enter your access token: ").strip()
    if not access_token:
        print("Error: Access token is required")
        sys.exit(1)
    
    # Initialize tester
    tester = UserProfileAPITester()
    tester.set_auth_token(access_token)
    
    # Run tests
    try:
        results = tester.run_all_tests()
        print("\nTests completed successfully!")
        
        # Check if all tests passed
        all_passed = (
            results["profile_test"]["success"] and
            results["update_test"]["success"] and
            results["validation_tests"]["invalid_email"]["success"] and
            results["validation_tests"]["weak_password"]["success"] and
            results["validation_tests"]["password_mismatch"]["success"]
        )
        
        if all_passed:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. Check the logs above for details.")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
