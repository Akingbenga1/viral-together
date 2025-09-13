# Admin Users Management API Endpoints

This document describes the admin user management endpoints that allow administrators and super administrators to manage any user's profile information and password.

## Endpoints Overview

### Base URL
All endpoints are prefixed with `/admin`

### Authentication & Authorization
All endpoints require:
- Authentication via Bearer token in the Authorization header
- User must have either `admin` or `super_admin` role

```
Authorization: Bearer <your_admin_access_token>
```

## Available Endpoints

### 1. List All Users
**GET** `/admin/users`

Retrieves a list of all users in the system for administrative purposes.

**Response:**
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john.doe@example.com",
    "mobile_number": "+1234567890",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
]
```

### 2. Get User Profile
**GET** `/admin/users/{user_id}/profile`

Retrieves a specific user's profile information.

**Parameters:**
- **user_id**: ID of the user whose profile to retrieve

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

### 3. Update User Profile
**PUT** `/admin/users/{user_id}/profile_update`

Updates any user's profile information and password. All fields are optional.

**Parameters:**
- **user_id**: ID of the user whose profile will be updated

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "mobile_number": "+1234567890",
  "username": "johndoe",
  "new_password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

**Response:**
```json
{
  "message": "User profile updated successfully by admin admin_user",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john.doe@example.com",
    "mobile_number": "+1234567890",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "updated_by": "admin_user"
}
```

**Validation Rules:**
- `first_name`, `last_name`, and `username`: Cannot be empty strings
- `email`: Must be a valid email format and unique across all users
- `mobile_number`: Must be at least 10 digits (spaces, dashes, parentheses are allowed)

**Password Requirements (if updating password):**
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

### 403 Forbidden
```json
{
  "detail": "Access denied. Admin or Super Admin privileges required."
}
```

### 404 Not Found
```json
{
  "detail": "Target user not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Email address is already in use"
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

## Security Features

1. **Role-Based Access Control**: Only `admin` and `super_admin` roles can access these endpoints
2. **Authentication Required**: All endpoints require valid authentication
3. **Admin Audit Trail**: All updates are logged with the admin user who performed the action
4. **Input Validation**: Comprehensive validation for all input fields
5. **Email/Username Uniqueness**: Email addresses and usernames must be unique across all users
6. **Password Strength**: Enforced password complexity requirements
7. **No Current Password Required**: Admins can update passwords without knowing the current password

## Testing

### Using HTTP Files
Use the provided `admin_users.http` file with your REST client (VS Code REST Client, IntelliJ HTTP Client, etc.).

### Using Python Test Script
Run the test script:
```bash
python run_admin_users_tests.py
```

You'll need to provide a valid admin/super_admin access token when prompted.

### Manual Testing with curl

1. **List All Users:**
```bash
curl -X GET "http://localhost:8000/admin/users" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

2. **Get User Profile:**
```bash
curl -X GET "http://localhost:8000/admin/users/1/profile" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

3. **Update User Profile:**
```bash
curl -X PUT "http://localhost:8000/admin/users/1/profile_update" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }'
```

4. **Update User Profile with Password:**
```bash
curl -X PUT "http://localhost:8000/admin/users/1/profile_update" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
  }'
```

## Implementation Details

### Files Created/Modified:
- `app/api/admin/__init__.py` - Admin module initialization
- `app/api/admin/admin_user_models.py` - Pydantic models for admin requests/responses
- `app/api/admin/admin_users.py` - Main admin API endpoint implementation
- `app/services/user_service.py` - Added admin-specific service methods
- `app/main.py` - Router registration for admin endpoints
- `api-test/api_endpoint_test/admin_users.http` - HTTP test file
- `api-test/api_test_script_runner/run_admin_users_tests.py` - Python test script

### Key Differences from Regular User Endpoints:
1. **No Current Password Required**: Admins can update passwords without knowing the current password
2. **Username Updates**: Admins can update usernames (regular users cannot)
3. **Any User Access**: Admins can update any user's profile, not just their own
4. **Audit Trail**: All admin actions are logged with the admin user who performed them
5. **Role-Based Access**: Only admin and super_admin roles can access these endpoints
6. **Combined Profile and Password Update**: Single endpoint handles both profile and password updates

## Usage in Frontend

The frontend can now use these endpoints to implement admin user management:

```typescript
// Update any user's profile (admin only)
const adminUpdateUserProfile = async (userId: number, profileData: {
  first_name?: string;
  last_name?: string;
  email?: string;
  mobile_number?: string;
  username?: string;
}) => {
  const response = await fetch(`/admin/users/${userId}/profile_update`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });
  return response.json();
};

// Update any user's profile with password (admin only)
const adminUpdateUserProfileWithPassword = async (userId: number, profileData: {
  first_name?: string;
  last_name?: string;
  email?: string;
  mobile_number?: string;
  username?: string;
  new_password?: string;
  confirm_password?: string;
}) => {
  const response = await fetch(`/admin/users/${userId}/profile_update`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });
  return response.json();
};

// List all users (admin only)
const adminListUsers = async () => {
  const response = await fetch('/admin/users', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

## Security Considerations

1. **Admin Access Logging**: All admin actions are logged for audit purposes
2. **Role Verification**: Endpoints verify admin/super_admin roles before allowing access
3. **Input Sanitization**: All inputs are validated and sanitized
4. **Password Security**: Passwords are hashed using secure algorithms
5. **Unique Constraints**: Email and username uniqueness is enforced
6. **Error Handling**: Comprehensive error handling prevents information leakage
