# API Test Script Runner

This directory contains automated test scripts for testing the Viral Together API endpoints.

## Available Test Scripts

### Individual Test Scripts
- `run_ai_agent_tests.py` - Tests AI Agent endpoints
- `run_business_tests.py` - Tests Business endpoints  
- `run_influencer_tests.py` - Tests Influencer endpoints
- `run_promotion_tests.py` - Tests Promotion endpoints
- `run_recommendations_tests.py` - Tests Recommendations endpoints

### Master Test Runner
- `run_all_tests.py` - Master script to run multiple test suites
- `run_all_tests.bat` - Windows batch script for easy execution
- `run_all_tests.sh` - Unix/Linux/Mac shell script for easy execution

## How to Use

### Running Individual Test Scripts

```bash
# Run all tests in a script
python run_promotion_tests.py http://localhost:8000

# Run a specific test number
python run_promotion_tests.py http://localhost:8000 1

# Run with default localhost URL
python run_promotion_tests.py
```

### Running Multiple Test Suites

#### Using Python Master Script
```bash
# Run all test suites
python run_all_tests.py http://localhost:8000

# Run specific test suites
python run_all_tests.py http://localhost:8000 business promotion

# Run with default localhost URL
python run_all_tests.py
```

#### Using Windows Batch Script
```cmd
# Run all test suites
run_all_tests.bat

# Run specific test suites
run_all_tests.bat business promotion

# Run with custom URL
run_all_tests.bat http://localhost:8000 ai_agent influencer
```

#### Using Unix/Linux/Mac Shell Script
```bash
# Make executable first
chmod +x run_all_tests.sh

# Run all test suites
./run_all_tests.sh

# Run specific test suites
./run_all_tests.sh business promotion

# Run with custom URL
./run_all_tests.sh http://localhost:8000 ai_agent influencer
```

## Test Suite Names

Available test suites for the master runner:
- `ai_agent` - AI Agent endpoints
- `business` - Business endpoints
- `influencer` - Influencer endpoints
- `promotion` - Promotion endpoints
- `recommendations` - Recommendations endpoints

## Features

### Individual Test Scripts
- ✅ Automatic authentication
- ✅ Retry logic for rate limiting and connection errors
- ✅ Comprehensive error testing
- ✅ Detailed test summaries
- ✅ Individual test execution support
- ✅ Response time tracking

### Master Test Runner
- ✅ Run all test suites or specific ones
- ✅ Parallel execution of test suites
- ✅ Comprehensive master summary
- ✅ Timeout protection (5 minutes per suite)
- ✅ Cross-platform support (Windows batch + Unix shell)
- ✅ Detailed failure reporting

## Test Results

Each test script provides:
- **Total Tests**: Number of tests executed
- **Successful Tests**: Number of passing tests
- **Failed Tests**: Number of failing tests
- **Success Rate**: Percentage of successful tests
- **Average Response Time**: Average API response time
- **Failed Test Details**: Specific details about failed tests

## Prerequisites

1. **API Server Running**: Ensure the FastAPI server is running on the specified URL
2. **Database Seeded**: Ensure the database has test data (users, businesses, influencers, etc.)
3. **Python Dependencies**: Install required packages:
   ```bash
   pip install requests
   ```

## Authentication

All test scripts will prompt you for database authentication credentials when running:
- Username: You will be prompted to enter your database authentication username
- Password: You will be prompted to enter your database authentication password

## Troubleshooting

### Common Issues

1. **Connection Errors**: Ensure the API server is running
2. **Authentication Failures**: Check if the test user exists in the database
3. **Test Data Issues**: Ensure the database has the required test data
4. **Rate Limiting**: Tests include retry logic for rate limiting

### Debug Mode

To see detailed output, run individual test scripts with specific test numbers:
```bash
python run_promotion_tests.py http://localhost:8000 1
```

## Adding New Test Scripts

To add a new test script:

1. Create a new Python file following the naming convention: `run_[module]_tests.py`
2. Implement the test class with:
   - `login()` method for authentication
   - `make_request()` method with retry logic
   - Individual test methods
   - `print_summary()` method
3. Add the script to the master runner's `test_suites` dictionary in `run_all_tests.py`

## Example Output

```
🎯 MASTER TEST RUNNER - Running All Test Suites
📍 Base URL: http://localhost:8000
🕐 Started at: 2024-01-15 14:30:00
================================================================================

🚀 Running BUSINESS Test Suite...
============================================================
🔐 Logging in...
✅ Login successful - Token: eyJhbGciOiJIUzI1NiIs...
1️⃣ Creating Public Business...
   Status: 200 | Time: 0.45s
...

📊 BUSINESS Test Suite: ✅ PASSED
   ⏱️  Execution Time: 12.34s
   🔢 Exit Code: 0

================================================================================
📊 MASTER TEST SUMMARY
================================================================================
Total Test Suites: 5
✅ Successful: 4
❌ Failed: 1
Success Rate: 80.0%

⏱️  Total Execution Time: 45.67s

🕐 Completed at: 2024-01-15 14:31:00

⚠️  1 TEST SUITE(S) FAILED
```
