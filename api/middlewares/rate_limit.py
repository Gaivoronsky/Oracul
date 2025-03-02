"""
Rate limiting middleware.
Implements rate limiting for API endpoints to prevent abuse.
"""

from fastapi import Request, HTTPException
import time
from typing import Dict, List, Tuple, Optional
import asyncio


class RateLimiter:
    """
    Simple in-memory rate limiter.
    """
    def __init__(self, rate_limit: int = 100, time_window: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            rate_limit: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
        self._cleanup_task = None

    async def _cleanup_old_requests(self):
        """
        Periodically clean up old request timestamps.
        """
        while True:
            await asyncio.sleep(self.time_window)
            current_time = time.time()
            for ip, timestamps in list(self.requests.items()):
                # Remove timestamps older than the time window
                self.requests[ip] = [ts for ts in timestamps if current_time - ts < self.time_window]
                # Remove empty entries
                if not self.requests[ip]:
                    del self.requests[ip]

    def start_cleanup_task(self):
        """
        Start the background task to clean up old request timestamps.
        """
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_requests())

    def stop_cleanup_task(self):
        """
        Stop the background cleanup task.
        """
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            self._cleanup_task = None

    def is_rate_limited(self, ip: str) -> Tuple[bool, Optional[int]]:
        """
        Check if the IP is rate limited.
        
        Args:
            ip: The IP address to check
            
        Returns:
            Tuple of (is_limited, retry_after)
        """
        current_time = time.time()
        
        # Initialize if this is the first request from this IP
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Remove timestamps older than the time window
        self.requests[ip] = [ts for ts in self.requests[ip] if current_time - ts < self.time_window]
        
        # Check if rate limit is exceeded
        if len(self.requests[ip]) >= self.rate_limit:
            # Calculate when the oldest request will expire
            oldest_timestamp = min(self.requests[ip])
            retry_after = int(self.time_window - (current_time - oldest_timestamp))
            return True, max(1, retry_after)
        
        # Add the current request timestamp
        self.requests[ip].append(current_time)
        return False, None


class RateLimitMiddleware:
    """
    Middleware for rate limiting API requests.
    """
    def __init__(
        self,
        rate_limit: int = 100,
        time_window: int = 60,
        exclude_paths: List[str] = None
    ):
        """
        Initialize the rate limit middleware.
        
        Args:
            rate_limit: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
            exclude_paths: List of paths to exclude from rate limiting
        """
        self.rate_limiter = RateLimiter(rate_limit, time_window)
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json"]
        
    async def __call__(self, request: Request, call_next):
        """
        Process the request and apply rate limiting.
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if rate limited
        is_limited, retry_after = self.rate_limiter.is_rate_limited(client_ip)
        if is_limited:
            headers = {"Retry-After": str(retry_after)}
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers=headers
            )
        
        # Process the request
        return await call_next(request)