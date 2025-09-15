#!/usr/bin/env python3
"""
Master API Test Runner - Run Multiple Test Suites
This script can run all test suites or specific ones based on command line arguments.
"""

import subprocess
import sys
import time
import os
import logging
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestSuiteResult:
    name: str
    success: bool
    exit_code: int
    execution_time: float
    output: str = ""

class MasterTestRunner:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_suites = {
            "ai_agent": "run_ai_agent_tests.py",
            "business": "run_business_tests.py", 
            "influencer": "run_influencer_tests.py",
            "promotion": "run_promotion_tests.py",
            "recommendations": "run_recommendations_tests.py",
            "unified_influencer_profile": "run_unified_influencer_profile_tests.py"
        }
        self.results: List[TestSuiteResult] = []
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger('master_test_runner')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_test_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"master_test_runner_{timestamp}.log"
        log_path = os.path.join(log_dir, log_filename)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        print(f"📝 Master runner logging to file: {log_path}")
        
    def run_single_test_suite(self, suite_name: str) -> TestSuiteResult:
        """Run a single test suite and return the result"""
        if suite_name not in self.test_suites:
            self.logger.error(f"Test suite '{suite_name}' not found")
            return TestSuiteResult(
                name=suite_name,
                success=False,
                exit_code=1,
                execution_time=0.0,
                output=f"Test suite '{suite_name}' not found"
            )
        
        script_path = self.test_suites[suite_name]
        start_time = time.time()
        
        # Log test suite execution start
        self.logger.info("=" * 80)
        self.logger.info(f"STARTING TEST SUITE: {suite_name.upper()}")
        self.logger.info(f"SCRIPT: {script_path}")
        self.logger.info(f"BASE URL: {self.base_url}")
        self.logger.info("-" * 80)
        
        print(f"\n🚀 Running {suite_name.upper()} Test Suite...")
        print("=" * 60)
        
        try:
            # Run the test script as a subprocess
            result = subprocess.run(
                [sys.executable, script_path, self.base_url],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per test suite
            )
            
            execution_time = time.time() - start_time
            success = result.returncode == 0
            
            # Format the output
            output_lines = []
            if result.stdout:
                output_lines.extend(result.stdout.split('\n'))
            if result.stderr:
                output_lines.extend([f"ERROR: {line}" for line in result.stderr.split('\n')])
            
            output = '\n'.join(output_lines)
            
            # Log test suite execution results
            self.logger.info(f"TEST SUITE COMPLETED: {suite_name.upper()}")
            self.logger.info(f"SUCCESS: {success}")
            self.logger.info(f"EXIT CODE: {result.returncode}")
            self.logger.info(f"EXECUTION TIME: {execution_time:.3f}s")
            self.logger.info(f"STDOUT LENGTH: {len(result.stdout) if result.stdout else 0} characters")
            self.logger.info(f"STDERR LENGTH: {len(result.stderr) if result.stderr else 0} characters")
            self.logger.info("=" * 80)
            
            return TestSuiteResult(
                name=suite_name,
                success=success,
                exit_code=result.returncode,
                execution_time=execution_time,
                output=output
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.error(f"TEST SUITE TIMEOUT: {suite_name.upper()}")
            self.logger.error(f"EXECUTION TIME: {execution_time:.3f}s")
            self.logger.info("=" * 80)
            return TestSuiteResult(
                name=suite_name,
                success=False,
                exit_code=1,
                execution_time=execution_time,
                output=f"Test suite '{suite_name}' timed out after 5 minutes"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"TEST SUITE ERROR: {suite_name.upper()}")
            self.logger.error(f"ERROR: {str(e)}")
            self.logger.error(f"EXECUTION TIME: {execution_time:.3f}s")
            self.logger.info("=" * 80)
            return TestSuiteResult(
                name=suite_name,
                success=False,
                exit_code=1,
                execution_time=execution_time,
                output=f"Error running test suite '{suite_name}': {str(e)}"
            )
    
    def run_all_test_suites(self) -> List[TestSuiteResult]:
        """Run all test suites"""
        print("🎯 MASTER TEST RUNNER - Running All Test Suites")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for suite_name in self.test_suites.keys():
            result = self.run_single_test_suite(suite_name)
            self.results.append(result)
            
            # Print summary for this suite
            status = "✅ PASSED" if result.success else "❌ FAILED"
            print(f"\n📊 {suite_name.upper()} Test Suite: {status}")
            print(f"   ⏱️  Execution Time: {result.execution_time:.2f}s")
            print(f"   🔢 Exit Code: {result.exit_code}")
            
            # Add a separator between test suites
            if suite_name != list(self.test_suites.keys())[-1]:
                print("\n" + "-" * 80)
        
        return self.results
    
    def run_specific_test_suites(self, suite_names: List[str]) -> List[TestSuiteResult]:
        """Run specific test suites"""
        print("🎯 MASTER TEST RUNNER - Running Specific Test Suites")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🎯 Test Suites: {', '.join(suite_names)}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for suite_name in suite_names:
            if suite_name in self.test_suites:
                result = self.run_single_test_suite(suite_name)
                self.results.append(result)
                
                # Print summary for this suite
                status = "✅ PASSED" if result.success else "❌ FAILED"
                print(f"\n📊 {suite_name.upper()} Test Suite: {status}")
                print(f"   ⏱️  Execution Time: {result.execution_time:.2f}s")
                print(f"   🔢 Exit Code: {result.exit_code}")
                
                # Add a separator between test suites
                if suite_name != suite_names[-1]:
                    print("\n" + "-" * 80)
            else:
                print(f"❌ Test suite '{suite_name}' not found. Available suites: {', '.join(self.test_suites.keys())}")
        
        return self.results
    
    def print_master_summary(self):
        """Print comprehensive summary of all test suites"""
        print("\n" + "=" * 80)
        print("📊 MASTER TEST SUMMARY")
        print("=" * 80)
        
        total_suites = len(self.results)
        successful_suites = sum(1 for result in self.results if result.success)
        failed_suites = total_suites - successful_suites
        
        print(f"Total Test Suites: {total_suites}")
        print(f"✅ Successful: {successful_suites}")
        print(f"❌ Failed: {failed_suites}")
        print(f"Success Rate: {(successful_suites/total_suites)*100:.1f}%")
        
        # Calculate total execution time
        total_execution_time = sum(result.execution_time for result in self.results)
        print(f"\n⏱️  Total Execution Time: {total_execution_time:.2f}s")
        
        # Detailed results
        if failed_suites > 0:
            print("\n❌ Failed Test Suites:")
            for result in self.results:
                if not result.success:
                    print(f"   - {result.name.upper()}: Exit Code {result.exit_code}")
                    if result.output:
                        # Show first few lines of output for failed tests
                        output_lines = result.output.split('\n')[:5]
                        for line in output_lines:
                            if line.strip():
                                print(f"     {line}")
                        if len(result.output.split('\n')) > 5:
                            print(f"     ... (truncated)")
        
        print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Overall status
        if failed_suites == 0:
            print("\n🎉 ALL TEST SUITES PASSED! 🎉")
        else:
            print(f"\n⚠️  {failed_suites} TEST SUITE(S) FAILED")

def main():
    """Main function to run the master test runner"""
    # Default URL (change this line to modify default URL)
    DEFAULT_BASE_URL = "http://localhost:8000"
    
    # Parse command line arguments
    base_url = DEFAULT_BASE_URL
    test_suites = []
    custom_url = None
    
    # Check for custom URL and test suites in arguments
    for arg in sys.argv[1:]:
        if arg.startswith("http"):
            custom_url = arg
        else:
            test_suites.append(arg)
    
    # Use custom URL if provided
    if custom_url:
        base_url = custom_url
        print(f"🔧 Using custom URL from command line: {base_url}")
    else:
        print(f"📍 Using default URL: {base_url}")
    
    # Show usage if no arguments provided
    if len(sys.argv) == 1:
        print("🎯 MASTER API TEST RUNNER")
        print("=" * 50)
        print("Usage:")
        print("  python run_all_tests.py [test_suite1] [test_suite2] ...")
        print("  python run_all_tests.py [base_url] [test_suite1] [test_suite2] ...")
        print("  python run_all_tests.py                    # Run all test suites")
        print("  python run_all_tests.py business promotion  # Run specific suites")
        print("  python run_all_tests.py http://localhost:8000 business promotion  # Run specific suites with custom URL")
        print("\nAvailable test suites:")
        print("  ai_agent      - AI Agent endpoints")
        print("  business      - Business endpoints")
        print("  influencer    - Influencer endpoints")
        print("  promotion     - Promotion endpoints")
        print("  recommendations - Recommendations endpoints")
        print("  unified_influencer_profile - Unified Influencer Profile endpoints")
        print("\nExamples:")
        print("  python run_all_tests.py")
        print("  python run_all_tests.py business promotion")
        print("  python run_all_tests.py http://localhost:8000 ai_agent influencer")
        print("  python run_all_tests.py unified_influencer_profile")
        print(f"\nDefault URL: {DEFAULT_BASE_URL}")
        print("To change default URL, modify DEFAULT_BASE_URL in the script")
        sys.exit(1)
    
    # Validate base_url format
    if not base_url.startswith(('http://', 'https://')):
        print("❌ Error: Base URL must start with http:// or https://")
        print(f"   Provided: {base_url}")
        sys.exit(1)
    
    runner = MasterTestRunner(base_url)
    
    # Run tests based on arguments
    if test_suites:
        # Run specific test suites
        runner.run_specific_test_suites(test_suites)
    else:
        # Run all test suites
        runner.run_all_test_suites()
    
    # Print master summary
    runner.print_master_summary()
    
    # Exit with appropriate code
    failed_suites = sum(1 for result in runner.results if not result.success)
    sys.exit(1 if failed_suites > 0 else 0)

if __name__ == "__main__":
    main()
