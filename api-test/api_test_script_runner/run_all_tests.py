#!/usr/bin/env python3
"""
Master API Test Runner - Run Multiple Test Suites
This script can run all test suites or specific ones based on command line arguments.
"""

import subprocess
import sys
import time
import os
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
            "recommendations": "run_recommendations_tests.py"
        }
        self.results: List[TestSuiteResult] = []
        
    def run_single_test_suite(self, suite_name: str) -> TestSuiteResult:
        """Run a single test suite and return the result"""
        if suite_name not in self.test_suites:
            return TestSuiteResult(
                name=suite_name,
                success=False,
                exit_code=1,
                execution_time=0.0,
                output=f"Test suite '{suite_name}' not found"
            )
        
        script_path = self.test_suites[suite_name]
        start_time = time.time()
        
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
            
            return TestSuiteResult(
                name=suite_name,
                success=success,
                exit_code=result.returncode,
                execution_time=execution_time,
                output=output
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestSuiteResult(
                name=suite_name,
                success=False,
                exit_code=1,
                execution_time=execution_time,
                output=f"Test suite '{suite_name}' timed out after 5 minutes"
            )
        except Exception as e:
            execution_time = time.time() - start_time
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
    # Check command line arguments
    if len(sys.argv) < 2:
        print("🎯 MASTER API TEST RUNNER")
        print("=" * 50)
        print("Usage:")
        print("  python run_all_tests.py [base_url] [test_suite1] [test_suite2] ...")
        print("  python run_all_tests.py                    # Run all test suites")
        print("  python run_all_tests.py http://localhost:8000  # Run all with custom URL")
        print("  python run_all_tests.py http://localhost:8000 business promotion  # Run specific suites")
        print("\nAvailable test suites:")
        print("  ai_agent      - AI Agent endpoints")
        print("  business      - Business endpoints")
        print("  influencer    - Influencer endpoints")
        print("  promotion     - Promotion endpoints")
        print("  recommendations - Recommendations endpoints")
        print("\nExamples:")
        print("  python run_all_tests.py")
        print("  python run_all_tests.py http://localhost:8000")
        print("  python run_all_tests.py business promotion")
        print("  python run_all_tests.py http://localhost:8000 ai_agent influencer")
        sys.exit(1)
    
    # Parse arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_suites = sys.argv[2:] if len(sys.argv) > 2 else []
    
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
