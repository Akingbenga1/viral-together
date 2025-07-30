# Viral Together - Test Suite

This directory contains a comprehensive test suite for the Viral Together application, implementing modern testing practices and patterns.

## Test Structure

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── unit/                           # Unit tests for individual components
│   ├── test_auth.py               # Authentication & authorization tests
│   ├── test_business.py           # Business entity tests
│   ├── test_influencer_improved.py # Improved influencer tests
│   ├── test_rate_card.py          # Rate card functionality tests
│   └── test_error_handling.py     # Error handling & edge cases
├── integration/                    # Integration tests
│   └── test_collaboration_workflow.py # End-to-end workflow tests
└── README.md                       # This file
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Authentication Tests (`test_auth.py`)**
- User registration (success, duplicates, validation)
- User login (valid/invalid credentials)
- Token validation and expiration
- Password security and hashing
- Complete authentication workflows

**Business Tests (`test_business.py`)**
- Business creation, retrieval, update, deletion
- Data validation and error handling
- Authorization and access control
- Search and filtering functionality

**Influencer Tests (`test_influencer_improved.py`)**
- Influencer profile management
- Availability settings
- Search by location and language
- Rate card associations
- Complete CRUD operations

**Rate Card Tests (`test_rate_card.py`)**
- Rate card creation and management
- Platform and content type validation
- Pricing tier management
- Currency and numeric validation

**Error Handling Tests (`test_error_handling.py`)**
- Input validation errors
- Authentication and authorization errors
- Database constraint violations
- System-level error handling
- Security vulnerability protection

### 2. Integration Tests (`tests/integration/`)

**Collaboration Workflow Tests**
- Complete business-to-influencer collaboration flow
- Promotion creation and management
- Interest expression and collaboration acceptance
- Multi-party interactions
- Cross-entity authorization

## Key Features

### Modern Test Architecture
- **Centralized Configuration**: All test setup in `conftest.py`
- **Factory Pattern**: Clean test data generation with `TestDataFactory`
- **Proper Fixtures**: Reusable, well-scoped test fixtures
- **Database Isolation**: Each test runs with a clean database state

### Comprehensive Coverage
- **Happy Path Testing**: All major functionality covered
- **Error Condition Testing**: Extensive error handling validation
- **Edge Case Testing**: Boundary conditions and unusual inputs
- **Security Testing**: SQL injection, XSS, and authorization bypass protection
- **Integration Testing**: Cross-module workflow validation

### Best Practices Implementation
- **No Global Variables**: Proper dependency injection throughout
- **ORM-Based Data Setup**: Using SQLAlchemy models instead of raw SQL
- **Async/Await Support**: Full async test support with pytest-asyncio
- **Proper Assertions**: Comprehensive response validation
- **Clean Test Data**: Factory-generated realistic test data

## Running Tests

### Prerequisites
```bash
# Install all dependencies (includes testing packages)
pip install -r requirements.txt

# OR install only basic testing dependencies
pip install pytest pytest-asyncio pytest-cov httpx faker aiosqlite

# Optional: Install enhanced testing tools
pip install -r requirements-test.txt

# Set up test database
export TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db"
```

### Run All Tests
```bash
# Run the entire test suite
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test class
pytest tests/unit/test_auth.py::TestUserRegistration

# Run specific test method
pytest tests/unit/test_auth.py::TestUserRegistration::test_register_new_user_success
```

### Run Tests with Filtering
```bash
# Run tests matching a pattern
pytest tests/ -k "auth"

# Run tests with specific markers
pytest tests/ -m "asyncio"

# Skip slow tests
pytest tests/ -m "not slow"
```

## Dependencies and Installation

### Requirements Files
The project uses multiple requirements files for different purposes:

- **`requirements.txt`**: Core dependencies including essential testing packages
- **`requirements-test.txt`**: Optional enhanced testing tools and development utilities

### Installation Options
```bash
# Option 1: Install everything (recommended for development)
pip install -r requirements.txt -r requirements-test.txt

# Option 2: Install only production + basic testing
pip install -r requirements.txt

# Option 3: Minimal testing setup
pip install pytest pytest-asyncio pytest-cov httpx faker aiosqlite
```

### Key Testing Packages Included

**Essential Testing (in requirements.txt):**
- `pytest>=7.4.0` - Main testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-xdist>=3.5.0` - Parallel test execution
- `httpx>=0.25.0` - HTTP client for API testing
- `faker>=20.0.0` - Test data generation
- `aiosqlite>=0.19.0` - SQLite async driver for testing

**Enhanced Testing (in requirements-test.txt):**
- `pytest-sugar` - Better test output formatting
- `pytest-html` - HTML test reports
- `black`, `flake8`, `isort` - Code quality tools
- `factory-boy` - Advanced test data factories
- `responses` - HTTP response mocking

## Test Configuration

### Environment Variables
```bash
# Test database URL (defaults to SQLite in-memory)
TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db"

# Test environment flag
TESTING=true

# Log level for tests
LOG_LEVEL=INFO
```

### Fixtures Available

**Database Fixtures**
- `db_session`: Clean database session for each test
- `reset_database`: Automatic database cleanup between tests

**Authentication Fixtures**
- `test_user`: Pre-created test user with known credentials
- `auth_token`: Valid JWT token for the test user
- `authenticated_client`: HTTP client with authentication headers

**Entity Fixtures**
- `test_business`: Pre-created business entity
- `test_influencer`: Pre-created influencer entity
- `test_factory`: Factory for generating test data

**HTTP Client Fixtures**
- `client`: Basic HTTP client for API testing
- `authenticated_client`: Pre-authenticated HTTP client

## Test Data Management

### Factory Pattern Usage
```python
# Generate user data
user_data = test_factory.user_data()
user_data = test_factory.user_data(username="specific_username")

# Generate business data
business_data = test_factory.business_data(user_id=user.id)

# Generate influencer data
influencer_data = test_factory.influencer_data(user_id=user.id)
```

### Custom Test Data
```python
# Override specific fields
custom_data = test_factory.user_data(
    username="testuser",
    email="test@example.com"
)
```

## Writing New Tests

### Test Class Structure
```python
class TestFeatureName:
    """Test cases for feature functionality."""

    @pytest.mark.asyncio
    async def test_feature_success(self, authenticated_client, test_factory):
        """Test successful feature operation."""
        # Arrange
        test_data = test_factory.feature_data()
        
        # Act
        response = await authenticated_client.post("/endpoint", json=test_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["field"] == test_data["field"]
```

### Test Naming Convention
- **Classes**: `TestFeatureName` (PascalCase)
- **Methods**: `test_action_condition_result` (snake_case)
- **Files**: `test_module_name.py` (snake_case)

### Test Categories by Method Name
- `test_*_success`: Happy path scenarios
- `test_*_fails`: Error conditions
- `test_*_invalid_*`: Validation failures
- `test_*_unauthorized_*`: Authorization failures
- `test_*_nonexistent_*`: Resource not found scenarios

## Continuous Integration

### GitHub Actions Integration
```yaml
# Example CI configuration
- name: Run Tests
  run: |
    pytest tests/ --cov=app --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Ensure test database URL is set
export TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db"

# Check database permissions
ls -la test.db
```

**Async Test Failures**
```python
# Ensure proper async/await usage
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

**Fixture Dependency Issues**
```python
# Check fixture scope and dependencies
@pytest.fixture(scope="function")  # Correct scope
async def dependent_fixture(base_fixture):
    # Proper dependency declaration
    pass
```

### Performance Optimization

**Parallel Test Execution**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/ -n auto
```

**Database Optimization**
```python
# Use in-memory database for faster tests
TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

## Migration from Old Tests

The old test file (`test_influencers.py`) has been replaced with this improved structure. Key improvements:

1. **Eliminated Global Variables**: No more `test_user` global variable
2. **Proper Fixture Usage**: Consistent fixture patterns throughout
3. **ORM-Based Setup**: Using SQLAlchemy models instead of raw SQL
4. **Comprehensive Coverage**: All API endpoints and error conditions
5. **Better Organization**: Logical grouping of related tests
6. **Modern Patterns**: Factory pattern for test data generation

## Contributing

### Adding New Tests
1. Follow the established patterns in existing test files
2. Use the factory pattern for test data generation
3. Include both success and failure scenarios
4. Add comprehensive assertions
5. Document complex test scenarios

### Test Review Checklist
- [ ] Tests follow naming conventions
- [ ] Both success and failure cases covered
- [ ] Proper fixture usage
- [ ] No hardcoded test data
- [ ] Comprehensive assertions
- [ ] Documentation for complex scenarios

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites) 