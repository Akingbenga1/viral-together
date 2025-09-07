#!/bin/bash

# Master API Test Runner - Unix/Linux/Mac Shell Script
# This script provides easy access to run all test suites or specific ones

echo "🎯 MASTER API TEST RUNNER - Unix/Linux/Mac Shell Script"
echo "========================================================"

# Default URL (change this line to modify default URL)
DEFAULT_BASE_URL="http://localhost:8000"

# Function to show usage
show_usage() {
    echo ""
    echo "Usage:"
    echo "  ./run_all_tests.sh [test_suite1] [test_suite2] ..."
    echo "  ./run_all_tests.sh [base_url] [test_suite1] [test_suite2] ..."
    echo ""
    echo "Examples:"
    echo "  ./run_all_tests.sh                           # Run all test suites"
    echo "  ./run_all_tests.sh business promotion        # Run specific suites"
    echo "  ./run_all_tests.sh http://localhost:8000 ai_agent influencer"
    echo ""
    echo "Available test suites:"
    echo "  ai_agent      - AI Agent endpoints"
    echo "  business      - Business endpoints"
    echo "  influencer    - Influencer endpoints"
    echo "  promotion     - Promotion endpoints"
    echo "  recommendations - Recommendations endpoints"
    echo ""
    echo "Default URL: $DEFAULT_BASE_URL"
    echo "To change default URL, modify DEFAULT_BASE_URL in the script"
    echo ""
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Set default base URL
BASE_URL="$DEFAULT_BASE_URL"
TEST_SUITES=""

# Check if first argument is a URL
if [[ $1 == http* ]]; then
    BASE_URL="$1"
    shift
    TEST_SUITES="$@"
    echo "🔧 Using custom URL: $BASE_URL"
else
    TEST_SUITES="$@"
    echo "📍 Using default URL: $BASE_URL"
fi

echo ""
echo "🚀 Starting Master Test Runner..."
echo "📍 Base URL: $BASE_URL"
if [ ! -z "$TEST_SUITES" ]; then
    echo "🎯 Test Suites: $TEST_SUITES"
fi
echo ""

# Run the master test runner
python3 run_all_tests.py "$BASE_URL" $TEST_SUITES

echo ""
echo "✅ Master Test Runner completed!"
