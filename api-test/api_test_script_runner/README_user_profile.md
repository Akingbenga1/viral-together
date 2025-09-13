# User Profile API Endpoints

This document describes the new user profile management endpoints that allow authenticated users to update their own profile information and password.

## Endpoints Overview

### Base URL
All endpoints are prefixed with `/user`

### Authentication
All endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## Available Endpoints

### 1. Get User Profile
**GET** `/user/profile`

Retrieves the current authenticated user's profile information.

**Response:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "mobile_number": "+1234567890",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 2. Update User Profile
**PUT** `/user/profile/update`

Updates the current authenticated user's profile information. All fields are optional.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "mobile_number": "+1234567890"
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john.doe@example.com",
    "mobile_number": "+1234567890",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Validation Rules:**
- `first_name` and `last_name`: Cannot be empty strings
- `email`: Must be a valid email format and unique across all users
- `mobile_number`: Must be at least 10 digits (spaces, dashes, parentheses are allowed)

### 3. Update User Password
**PUT** `/user/profile/password`

Updates the current authenticated user's password.

**Request Body:**
```json
{
  "current_password": "old_password_123",
  "new_password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

**Response:**
```json
{
  "message": "Password updated successfully",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john.doe@example.com",
    "mobile_number": "+1234567890",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

**Password Requirements:**
- At least 8 characters long
- Contains at least one uppercase letter
- Contains at least one lowercase letter
- Contains at least one digit
- `confirm_password` must match `new_password`

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 400 Bad Request
```json
{
  "detail": "Email address is already in use"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Testing

### Using HTTP Files
Use the provided `user_profile.http` file with your REST client (VS Code REST Client, IntelliJ HTTP Client, etc.).

### Using Python Test Script
Run the test script:
```bash
python run_user_profile_tests.py
```

You'll need to provide a valid access token when prompted.

### Manual Testing with curl

1. **Get Profile:**
```bash
curl -X GET "http://localhost:8000/user/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

2. **Update Profile:**
```bash
curl -X PUT "http://localhost:8000/user/profile/update" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }'
```

3. **Update Password:**
```bash
curl -X PUT "http://localhost:8000/user/profile/password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "old_password_123",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
  }'
```

## Security Features

1. **Authentication Required**: All endpoints require valid authentication
2. **Self-Update Only**: Users can only update their own profile
3. **Password Verification**: Password updates require current password verification
4. **Input Validation**: Comprehensive validation for all input fields
5. **Email Uniqueness**: Email addresses must be unique across all users
6. **Password Strength**: Enforced password complexity requirements

## Implementation Details

### Files Created/Modified:
- `app/api/users/user_profile.py` - Main API endpoint implementation
- `app/api/users/user_models.py` - Pydantic models for request/response
- `app/services/user_service.py` - Business logic for user operations
- `app/main.py` - Router registration
- `api-test/api_endpoint_test/user_profile.http` - HTTP test file
- `api-test/api_test_script_runner/run_user_profile_tests.py` - Python test script

### Dependencies:
- FastAPI for API framework
- SQLAlchemy for database operations
- Pydantic for data validation
- Passlib for password hashing
- Email-validator for email validation

## Usage in Frontend

The frontend can now use these endpoints to implement user profile management:

```typescript
// Update user profile
const updateProfile = async (profileData: {
  first_name?: string;
  last_name?: string;
  email?: string;
  mobile_number?: string;
}) => {
  const response = await fetch('/user/profile/update', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });
  return response.json();
};

// Update password
const updatePassword = async (passwordData: {
  current_password: string;
  new_password: string;
  confirm_password: string;
}) => {
  const response = await fetch('/user/profile/password', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(passwordData)
  });
  return response.json();
};
```
