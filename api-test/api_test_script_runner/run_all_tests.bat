@echo off
REM Master API Test Runner - Windows Batch Script
REM This script provides easy access to run all test suites or specific ones

echo 🎯 MASTER API TEST RUNNER - Windows Batch Script
echo ================================================

REM Default URL (change this line to modify default URL)
set DEFAULT_BASE_URL=http://localhost:8000

if "%1"=="" (
    echo.
    echo Usage:
    echo   run_all_tests.bat [test_suite1] [test_suite2] ...
    echo   run_all_tests.bat [base_url] [test_suite1] [test_suite2] ...
    echo.
    echo Examples:
    echo   run_all_tests.bat                           # Run all test suites
    echo   run_all_tests.bat business promotion        # Run specific suites
    echo   run_all_tests.bat http://localhost:8000 ai_agent influencer
    echo.
    echo Available test suites:
    echo   ai_agent      - AI Agent endpoints
    echo   business      - Business endpoints
    echo   influencer    - Influencer endpoints
    echo   promotion     - Promotion endpoints
    echo   recommendations - Recommendations endpoints
    echo.
    echo Default URL: %DEFAULT_BASE_URL%
    echo To change default URL, modify DEFAULT_BASE_URL in the script
    echo.
    pause
    exit /b 1
)

REM Set default base URL
set BASE_URL=%DEFAULT_BASE_URL%
if "%1:~0,4%"=="http" (
    set BASE_URL=%1
    set TEST_SUITES=%2 %3 %4 %5 %6
    echo 🔧 Using custom URL: %BASE_URL%
) else (
    set TEST_SUITES=%1 %2 %3 %4 %5 %6
    echo 📍 Using default URL: %BASE_URL%
)

echo.
echo 🚀 Starting Master Test Runner...
echo 📍 Base URL: %BASE_URL%
if not "%TEST_SUITES%"=="" (
    echo 🎯 Test Suites: %TEST_SUITES%
)
echo.

REM Run the master test runner
python run_all_tests.py %BASE_URL% %TEST_SUITES%

echo.
echo ✅ Master Test Runner completed!
pause
