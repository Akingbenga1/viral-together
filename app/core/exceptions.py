class AuthorizationError(Exception):
    """Raised when user is not authorized for an operation"""
    pass

class NotFoundError(Exception):
    """Raised when a resource is not found"""
    pass

class ValidationError(Exception):
    """Raised when data validation fails"""
    pass

class GeocodingError(Exception):
    """Raised when geocoding operations fail"""
    pass

class DuplicateLocationError(Exception):
    """Raised when trying to save a location with duplicate coordinates for the same entity"""
    pass
