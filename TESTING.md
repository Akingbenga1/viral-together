# Quick Testing Setup Guide

This guide helps you quickly set up the testing environment for Viral Together.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the automated setup script
python setup-dev.py --enhanced

# This will:
# - Install all dependencies
# - Set up environment variables
# - Configure pre-commit hooks
# - Run initial tests to verify setup
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # Optional enhanced tools

# 2. Set up environment
export TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db"
export TESTING=true

# 3. Run tests
python run_tests.py
```

## 📦 Dependencies Overview

### Core Testing Dependencies (requirements.txt)
```
pytest>=7.4.0                 # Main testing framework
pytest-asyncio>=0.21.0        # Async test support
pytest-cov>=4.1.0             # Coverage reporting
pytest-xdist>=3.5.0           # Parallel test execution
httpx>=0.25.0                 # HTTP client for API testing
faker>=20.0.0                 # Test data generation
aiosqlite>=0.19.0             # SQLite async driver for testing
```

### Enhanced Testing Tools (requirements-test.txt)
```
pytest-sugar>=0.9.7           # Better test output formatting
pytest-html>=4.1.0            # HTML test reports
black>=23.12.0                # Code formatting
flake8>=6.1.0                 # Code style checking
factory-boy>=3.3.0            # Advanced test data factories
responses>=0.24.0             # Mock HTTP responses
```

## 🧪 Running Tests

### Basic Commands
```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific test categories
python run_tests.py --auth      # Authentication tests
python run_tests.py --business  # Business logic tests
python run_tests.py --unit      # All unit tests
```

### Advanced Commands
```bash
# Run tests in parallel (faster)
python run_tests.py -n 4

# Generate HTML coverage report
python run_tests.py --html-coverage

# Run with debugging
python run_tests.py --pdb

# Clean artifacts and run tests
python run_tests.py --clean
```

### Direct pytest Commands
```bash
# Run specific test file
pytest tests/unit/test_auth.py -v

# Run specific test class
pytest tests/unit/test_auth.py::TestUserRegistration -v

# Run tests matching a pattern
pytest tests/ -k "auth" -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## 🔧 Development Tools

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Check code style
flake8 .

# Type checking
mypy app/

# Security check
bandit -r app/
```

### Pre-commit Hooks
```bash
# Install hooks (done automatically by setup-dev.py)
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📊 Coverage Reports

### Generate Coverage Reports
```bash
# Terminal coverage report
pytest tests/ --cov=app --cov-report=term-missing

# HTML coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# XML coverage for CI
pytest tests/ --cov=app --cov-report=xml
```

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Make sure you're in the project root
cd /path/to/viral-together

# Install dependencies
pip install -r requirements.txt
```

**Database Errors**
```bash
# Set test database URL
export TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db"

# Or use in-memory database (faster)
export TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

**Async Test Failures**
```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio

# Check for proper async/await usage in tests
```

### Getting Help
```bash
# View test runner options
python run_tests.py --help

# View setup script options
python setup-dev.py --help

# View pytest options
pytest --help
```

## 📁 Test Structure

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── unit/                           # Unit tests
│   ├── test_auth.py               # Authentication tests
│   ├── test_business.py           # Business logic tests
│   ├── test_influencer_improved.py # Influencer tests
│   ├── test_rate_card.py          # Rate card tests
│   └── test_error_handling.py     # Error handling tests
├── integration/                    # Integration tests
│   └── test_collaboration_workflow.py # End-to-end workflows
└── README.md                       # Detailed documentation
```

## 🎯 Next Steps

1. **Run the setup**: `python setup-dev.py --enhanced`
2. **Verify tests work**: `python run_tests.py --auth`
3. **Check coverage**: `python run_tests.py --coverage`
4. **Start developing**: Add new tests following the established patterns

For detailed documentation, see `tests/README.md`. 