#!/usr/bin/env python3
"""
Test runner script for Viral Together application.

This script provides an easy way to run tests with various configurations
and options without remembering complex pytest commands.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def setup_test_environment():
    """Set up environment variables for testing."""
    os.environ["TESTING"] = "true"
    
    # Set test database URL if not already set
    if "TEST_DATABASE_URL" not in os.environ:
        os.environ["TEST_DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    
    # Set log level for tests
    if "LOG_LEVEL" not in os.environ:
        os.environ["LOG_LEVEL"] = "INFO"


def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=False)


def main():
    parser = argparse.ArgumentParser(description="Run Viral Together tests")
    
    # Test selection options
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run only integration tests"
    )
    parser.add_argument(
        "--auth", 
        action="store_true", 
        help="Run only authentication tests"
    )
    parser.add_argument(
        "--business", 
        action="store_true", 
        help="Run only business tests"
    )
    parser.add_argument(
        "--influencer", 
        action="store_true", 
        help="Run only influencer tests"
    )
    parser.add_argument(
        "--error", 
        action="store_true", 
        help="Run only error handling tests"
    )
    
    # Output options
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--html-coverage", 
        action="store_true", 
        help="Generate HTML coverage report"
    )
    
    # Performance options
    parser.add_argument(
        "-n", "--parallel", 
        type=int, 
        help="Run tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        "--fast", 
        action="store_true", 
        help="Skip slow tests"
    )
    
    # Debug options
    parser.add_argument(
        "--pdb", 
        action="store_true", 
        help="Drop into debugger on failures"
    )
    parser.add_argument(
        "--lf", 
        action="store_true", 
        help="Run only last failed tests"
    )
    parser.add_argument(
        "--tb", 
        choices=["short", "long", "line", "native"], 
        default="short",
        help="Traceback style"
    )
    
    # Filter options
    parser.add_argument(
        "-k", "--keyword", 
        help="Run tests matching keyword expression"
    )
    parser.add_argument(
        "-m", "--marker", 
        help="Run tests with specific marker"
    )
    
    # Cleanup options
    parser.add_argument(
        "--clean", 
        action="store_true", 
        help="Clean test artifacts before running"
    )
    
    args = parser.parse_args()
    
    # Set up test environment
    setup_test_environment()
    
    # Clean artifacts if requested
    if args.clean:
        print("Cleaning test artifacts...")
        artifacts = ["test.db", ".coverage", "htmlcov/", ".pytest_cache/"]
        for artifact in artifacts:
            if os.path.exists(artifact):
                if os.path.isdir(artifact):
                    subprocess.run(["rm", "-rf", artifact])
                else:
                    os.remove(artifact)
                print(f"Removed {artifact}")
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Determine test path
    test_paths = []
    if args.unit:
        test_paths.append("tests/unit/")
    if args.integration:
        test_paths.append("tests/integration/")
    if args.auth:
        test_paths.append("tests/unit/test_auth.py")
    if args.business:
        test_paths.append("tests/unit/test_business.py")
    if args.influencer:
        test_paths.extend([
            "tests/unit/test_influencer_improved.py",
            "tests/unit/test_rate_card.py"
        ])
    if args.error:
        test_paths.append("tests/unit/test_error_handling.py")
    
    # If no specific tests selected, run all
    if not test_paths:
        test_paths = ["tests/"]
    
    cmd.extend(test_paths)
    
    # Add output options
    if args.verbose:
        cmd.append("-v")
    
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    if args.html_coverage:
        cmd.extend(["--cov=app", "--cov-report=html"])
    
    # Add performance options
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Add debug options
    if args.pdb:
        cmd.append("--pdb")
    
    if args.lf:
        cmd.append("--lf")
    
    cmd.extend(["--tb", args.tb])
    
    # Add filter options
    if args.keyword:
        cmd.extend(["-k", args.keyword])
    
    if args.marker:
        cmd.extend(["-m", args.marker])
    
    # Run the tests
    result = run_command(cmd)
    
    # Print summary
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        if args.coverage or args.html_coverage:
            print("📊 Coverage report generated")
            if args.html_coverage:
                print("🌐 HTML coverage report: htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code {result.returncode}")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main()) 