#!/usr/bin/env python3
"""
Automated API Test Runner for AI Agent Endpoints
This script automatically tests all endpoints defined in ai_agent_tests.http
"""

import requests
import json
import time
import sys
import getpass
import urllib.parse
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

class AIAgentAPITester:
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
        self.logger = logging.getLogger('ai_agent_api_tests')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"ai_agent_api_tests_{timestamp}.log"
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
                    expected_status: int = 200, use_form_data: bool = False) -> TestResult:
        """Make HTTP request and return test result"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if data and not use_form_data:
            headers["Content-Type"] = "application/json"
        
        # Log API request details
        self.logger.info("=" * 80)
        self.logger.info(f"API REQUEST: {method} {endpoint}")
        self.logger.info(f"FULL URL: {url}")
        self.logger.info(f"REQUEST HEADERS: {json.dumps(headers, indent=2)}")
        if data:
            if use_form_data:
                self.logger.info(f"REQUEST BODY (FORM DATA): {data}")
            else:
                self.logger.info(f"REQUEST BODY: {json.dumps(data, indent=2)}")
        else:
            self.logger.info("REQUEST BODY: None")
        self.logger.info("-" * 80)
        
        start_time = time.time()
        
        try:
            if use_form_data:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,  # Use data instead of json for form data
                    timeout=30
                )
            else:
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
        """Run all AI agent API tests"""
        print("🚀 Starting AI Agent API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        self._run_test_1_create_ai_agent()
        self._run_test_2_get_all_ai_agents()
        self._run_test_3_get_specific_ai_agent()
        self._run_test_4_record_agent_response()
        self._run_test_5_get_agent_responses()
        self._run_test_6_get_task_responses()
        self._run_test_7_create_user_agent_association()
        self._run_test_8_get_user_agents()
        self._run_test_9_get_agent_users()
        self._run_test_9_5_get_user_primary_agent()
        self._run_test_10_create_coordination_session()
        self._run_test_11_get_available_agents()
        self._run_test_12_get_agent_context()
        self._run_test_13_store_user_conversation()
        self._run_test_14_retrieve_user_conversations()
        self._run_test_15_get_conversation_history()
        
        return self.test_results
        
        # Individual test methods will be defined below
    
    def _run_test_1_create_ai_agent(self):
        """Test 1: Create AI Agent"""
        print("\n1️⃣ Creating AI Agent...")
        agent_types = ["chat_support", "marketing", "sales", "technical_support", "content_creation", "data_analysis"]
        capabilities_list = ["chat", "customer_support", "faq", "lead_generation", "content_writing", "data_processing", "automation", "analytics"]
        limitations_list = ["complex_technical_issues", "financial_advice", "legal_consultation", "medical_diagnosis", "personal_data_handling"]
        
        create_agent_data = {
            "name": f"{self.fake.random_element(elements=('Chat', 'Smart', 'AI', 'Digital', 'Virtual'))} {self.fake.random_element(elements=('Support', 'Assistant', 'Agent', 'Helper', 'Bot'))} {self.fake.random_int(min=1, max=1000)}",
            "agent_type": self.fake.random_element(elements=agent_types),
            "capabilities": {
                "capabilities": self.fake.random_elements(elements=capabilities_list, length=self.fake.random_int(min=2, max=5), unique=True),
                "limitations": self.fake.random_elements(elements=limitations_list, length=self.fake.random_int(min=1, max=3), unique=True)
            }
        }
        result = self.make_request("POST", "/ai-agents/", create_agent_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_get_all_ai_agents(self):
        """Test 2: Get All AI Agents"""
        print("\n2️⃣ Getting All AI Agents...")
        result = self.make_request("GET", "/ai-agents/")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_get_specific_ai_agent(self):
        """Test 3: Get Specific AI Agent"""
        print("\n3️⃣ Getting Specific AI Agent...")
        random_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/ai-agents/{random_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_record_agent_response(self):
        """Test 4: Record Agent Response"""
        print("\n4️⃣ Recording Agent Response...")
        response_types = ["task_response", "chat_message", "automated_reply", "system_notification", "error_message"]
        response_data = {
            "agent_id": self.fake.random_int(min=1, max=100),
            "task_id": f"task_{self.fake.random_int(min=1000, max=9999)}",
            "response": f"{self.fake.sentence()} {self.fake.sentence()}",
            "response_type": self.fake.random_element(elements=response_types)
        }
        result = self.make_request("POST", "/ai-agents/responses", response_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_5_get_agent_responses(self):
        """Test 5: Get Agent Responses"""
        print("\n5️⃣ Getting Agent Responses...")
        random_id = self.fake.random_int(min=1, max=100)
        random_limit = self.fake.random_int(min=5, max=50)
        result = self.make_request("GET", f"/ai-agents/responses/agent/{random_id}?limit={random_limit}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_6_get_task_responses(self):
        """Test 6: Get Task Responses"""
        print("\n6️⃣ Getting Task Responses...")
        random_task_id = f"task_{self.fake.random_int(min=1000, max=9999)}"
        result = self.make_request("GET", f"/ai-agents/responses/task/{random_task_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_7_create_user_agent_association(self):
        """Test 7: Create User-Agent Association"""
        print("\n7️⃣ Creating User-Agent Association...")
        association_types = ["primary", "secondary", "backup", "specialized", "temporary"]
        statuses = ["active", "inactive", "pending", "suspended"]
        association_data = {
            "user_id": self.fake.random_int(min=1, max=100),
            "agent_id": self.fake.random_int(min=1, max=100),
            "association_type": self.fake.random_element(elements=association_types),
            "is_primary": self.fake.boolean(),
            "priority": self.fake.random_int(min=1, max=10),
            "status": self.fake.random_element(elements=statuses),
            "assigned_by": self.fake.random_int(min=1, max=100)
        }
        result = self.make_request("POST", "/ai-agents/associations", association_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_8_get_user_agents(self):
        """Test 8: Get User's Agents"""
        print("\n8️⃣ Getting User's Agents...")
        random_user_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/ai-agents/associations/user/{random_user_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_get_agent_users(self):
        """Test 9: Get Agent's Users"""
        print("\n9️⃣ Getting Agent's Users...")
        random_agent_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/ai-agents/associations/agent/{random_agent_id}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_5_get_user_primary_agent(self):
        """Test 9.5: Get User's Primary Agent"""
        print("\n9️⃣5️⃣ Getting User's Primary Agent...")
        random_user_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/ai-agents/associations/user/{random_user_id}/primary")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_10_create_coordination_session(self):
        """Test 10: Create Coordination Session"""
        print("\n🔟 Creating Coordination Session...")
        task_types = ["customer_support", "technical_issue", "billing_inquiry", "product_question", "complaint", "feature_request"]
        priorities = ["low", "medium", "high", "urgent", "critical"]
        issues = ["Payment problem", "Login issue", "Feature request", "Bug report", "Account question", "Technical support"]
        
        coordination_data = {
            "user_id": self.fake.random_int(min=1, max=100),
            "task_type": self.fake.random_element(elements=task_types),
            "initial_context": {
                "customer_issue": self.fake.random_element(elements=issues),
                "priority": self.fake.random_element(elements=priorities)
            }
        }
        result = self.make_request("POST", "/ai-agents/coordination/sessions", coordination_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_11_get_available_agents(self):
        """Test 11: Get Available Agents"""
        print("\n1️⃣1️⃣ Getting Available Agents...")
        random_user_id = self.fake.random_int(min=1, max=100)
        capabilities = ["chat_support", "technical_support", "sales", "marketing", "data_analysis", "content_creation"]
        random_capability = self.fake.random_element(elements=capabilities)
        result = self.make_request("GET", f"/ai-agents/coordination/agents/{random_user_id}?capability={random_capability}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_12_get_agent_context(self):
        """Test 12: Get Agent Context"""
        print("\n1️⃣2️⃣ Getting Agent Context...")
        prompts = ["I need help with my payment", "How do I reset my password?", "Can you help me with my order?", "I have a technical issue", "I want to cancel my subscription"]
        context_data = {
            "user_id": self.fake.random_int(min=1, max=100),
            "current_prompt": self.fake.random_element(elements=prompts),
            "agent_id": self.fake.random_int(min=1, max=100),
            "context_window": self.fake.random_int(min=5, max=50)
        }
        result = self.make_request("POST", "/ai-agents/coordination/context", context_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_13_store_user_conversation(self):
        """Test 13: Store User Conversation"""
        print("\n1️⃣3️⃣ Storing User Conversation...")
        # The endpoint expects query parameters, not form data or JSON body
        user_messages = ["I need help with my payment", "How do I reset my password?", "Can you help me with my order?", "I have a technical issue", "I want to cancel my subscription"]
        agent_responses = ["I can help you with that. What specific issue are you experiencing?", "Let me assist you with that. Can you provide more details?", "I understand your concern. Let me look into this for you.", "I'll help you resolve this issue. Please give me a moment.", "I can definitely help you with that request."]
        conversation_types = ["customer_support", "technical_issue", "billing_inquiry", "product_question", "complaint"]
        
        user_message = self.fake.random_element(elements=user_messages)
        agent_response = self.fake.random_element(elements=agent_responses)
        conversation_text = f"User: {user_message}\nAgent: {agent_response}"
        
        # URL encode the conversation text to handle newlines and special characters
        encoded_text = urllib.parse.quote(conversation_text)
        random_user_id = self.fake.random_int(min=1, max=100)
        random_conversation_type = self.fake.random_element(elements=conversation_types)
        url = f"/ai-agents/conversations?user_id={random_user_id}&conversation_text={encoded_text}&conversation_type={random_conversation_type}"
        result = self.make_request("POST", url, None)  # No data body needed
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_14_retrieve_user_conversations(self):
        """Test 14: Retrieve User Conversations"""
        print("\n1️⃣4️⃣ Retrieving User Conversations...")
        random_user_id = self.fake.random_int(min=1, max=100)
        queries = ["payment", "password", "order", "technical", "subscription", "billing", "support"]
        conversation_types = ["customer_support", "technical_issue", "billing_inquiry", "product_question", "complaint"]
        random_query = self.fake.random_element(elements=queries)
        random_limit = self.fake.random_int(min=3, max=20)
        random_conversation_type = self.fake.random_element(elements=conversation_types)
        result = self.make_request("GET", f"/ai-agents/conversations/{random_user_id}?query={random_query}&limit={random_limit}&conversation_type={random_conversation_type}")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_15_get_conversation_history(self):
        """Test 15: Get Conversation History"""
        print("\n1️⃣5️⃣ Getting Conversation History...")
        random_user_id = self.fake.random_int(min=1, max=100)
        result = self.make_request("GET", f"/ai-agents/conversations/{random_user_id}/history")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Create AI Agent with Invalid Data
        print("\n❌ Creating AI Agent with Invalid Data...")
        invalid_data = {
            "name": "",
            "agent_type": "invalid_type",
            "capabilities": {},
            "user_id": self.fake.random_int(min=999, max=9999)
        }
        result = self.make_request("POST", "/ai-agents/", invalid_data, expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Get Non-existent Agent
        print("\n❌ Getting Non-existent Agent...")
        non_existent_id = self.fake.random_int(min=999, max=9999)
        result = self.make_request("GET", f"/ai-agents/{non_existent_id}", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Record Response for Non-existent Agent
        print("\n❌ Recording Response for Non-existent Agent...")
        invalid_response_data = {
            "agent_id": self.fake.random_int(min=999, max=9999),
            "task_id": f"task_{self.fake.random_int(min=1000, max=9999)}",
            "response": f"This should fail - {self.fake.sentence()}",
            "response_type": "task_response"
        }
        result = self.make_request("POST", "/ai-agents/responses", invalid_response_data, expected_status=404)
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
        elif arg.replace(".", "").isdigit():  # Handle decimal test numbers like "9.5"
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
        print("  python run_ai_agent_tests.py [test_number]")
        print("  python run_ai_agent_tests.py [base_url] [test_number]")
        print("  python run_ai_agent_tests.py                    # Run all tests")
        print("  python run_ai_agent_tests.py 8                  # Run only test 8")
        print("  python run_ai_agent_tests.py http://localhost:8000 8  # Run test 8 with custom URL")
        print("\nAvailable test numbers:")
        print("  1  - Create AI Agent")
        print("  2  - Get All AI Agents")
        print("  3  - Get Specific AI Agent")
        print("  4  - Record Agent Response")
        print("  5  - Get Agent Responses")
        print("  6  - Get Task Responses")
        print("  7  - Create User-Agent Association")
        print("  8  - Get User's Agents")
        print("  9  - Get Agent's Users")
        print("  9.5- Get User's Primary Agent")
        print("  10 - Create Coordination Session")
        print("  11 - Get Available Agents")
        print("  12 - Get Agent Context")
        print("  13 - Store User Conversation")
        print("  14 - Retrieve User Conversations")
        print("  15 - Get Conversation History")
        print(f"\nDefault URL: {DEFAULT_BASE_URL}")
        print("To change default URL, modify DEFAULT_BASE_URL in the script")
        sys.exit(1)
    
    tester = AIAgentAPITester(base_url)
    
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
            "1": tester._run_test_1_create_ai_agent,
            "2": tester._run_test_2_get_all_ai_agents,
            "3": tester._run_test_3_get_specific_ai_agent,
            "4": tester._run_test_4_record_agent_response,
            "5": tester._run_test_5_get_agent_responses,
            "6": tester._run_test_6_get_task_responses,
            "7": tester._run_test_7_create_user_agent_association,
            "8": tester._run_test_8_get_user_agents,
            "9": tester._run_test_9_get_agent_users,
            "9.5": tester._run_test_9_5_get_user_primary_agent,
            "10": tester._run_test_10_create_coordination_session,
            "11": tester._run_test_11_get_available_agents,
            "12": tester._run_test_12_get_agent_context,
            "13": tester._run_test_13_store_user_conversation,
            "14": tester._run_test_14_retrieve_user_conversations,
            "15": tester._run_test_15_get_conversation_history,
        }
        
        if test_number in test_methods:
            test_methods[test_number]()
        else:
            print(f"❌ Invalid test number: {test_number}")
            print("Available test numbers: 1, 2, 3, 4, 5, 6, 7, 8, 9, 9.5, 10, 11, 12, 13, 14, 15")
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
