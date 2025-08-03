import time
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class RateLimiter:
    def __init__(self):
        # Rate limiting storage: {ip_address: [(timestamp, count), ...]}
        self.rate_limit_storage: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
    
    def check_rate_limit(
        self, 
        ip_address: str, 
        max_requests: int = 3, 
        window_hours: int = 1
    ) -> bool:
        """
        Check if the IP address has exceeded the rate limit.
        Returns True if request is allowed, False if rate limited.
        """
        current_time = time.time()
        window_seconds = window_hours * 3600
        
        # Clean old entries (older than window)
        self.rate_limit_storage[ip_address] = [
            (timestamp, count) for timestamp, count in self.rate_limit_storage[ip_address]
            if current_time - timestamp < window_seconds
        ]
        
        # Count total requests in the window
        total_requests = sum(count for _, count in self.rate_limit_storage[ip_address])
        
        if total_requests >= max_requests:
            return False
        
        # Add current request
        self.rate_limit_storage[ip_address].append((current_time, 1))
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()



# Specific rate limiter for business creation
def business_creation_rate_limit(request: Request):
    """
    Dependency for rate limiting business creation endpoint.
    Limits to 3 requests per hour with custom error message.
    """
    client_ip = request.client.host
    
    if not rate_limiter.check_rate_limit(client_ip, max_requests=3, window_hours=1):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "You have exceeded the limit of 3 business profile creation requests per hour. Please try again later.",
                "limit": "3 requests per hour",
                "reset_time": "1 hour from now"
            }
        )
    
    return True

# Generic rate limiter dependency factory
def create_rate_limit_dependency(
    max_requests: int = 3,
    window_hours: int = 1,
    error_message: str = "Rate limit exceeded"
):
    """
    Factory function to create rate limiting dependencies.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_hours: Time window in hours
        error_message: Custom error message
    """
    def rate_limit_dependency(request: Request):
        client_ip = request.client.host
        
        if not rate_limiter.check_rate_limit(client_ip, max_requests, window_hours):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": error_message,
                    "limit": f"{max_requests} requests per {window_hours} hour(s)",
                    "reset_time": f"{window_hours} hour(s) from now"
                }
            )
        
        return True
    
    return rate_limit_dependency 