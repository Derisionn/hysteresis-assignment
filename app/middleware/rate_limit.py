"""Rate limiting middleware."""

import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store request timestamps per IP
        self.request_history: defaultdict[str, list[datetime]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Check rate limits
        now = datetime.now()
        self._cleanup_old_requests(client_ip, now)
        
        # Check minute limit
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            ts for ts in self.request_history[client_ip]
            if ts > minute_ago
        ]
        
        if len(recent_requests) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((minute_ago + timedelta(minutes=1)).timestamp()))
                }
            )
        
        # Check hour limit
        hour_ago = now - timedelta(hours=1)
        hourly_requests = [
            ts for ts in self.request_history[client_ip]
            if ts > hour_ago
        ]
        
        if len(hourly_requests) >= self.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour",
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": str(self.requests_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((hour_ago + timedelta(hours=1)).timestamp()))
                }
            )
        
        # Record request
        self.request_history[client_ip].append(now)
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(recent_requests) - 1
        )
        response.headers["X-RateLimit-Reset"] = str(
            int((minute_ago + timedelta(minutes=1)).timestamp())
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_ip: str, now: datetime):
        """Remove requests older than 1 hour."""
        hour_ago = now - timedelta(hours=1)
        self.request_history[client_ip] = [
            ts for ts in self.request_history[client_ip]
            if ts > hour_ago
        ]
        
        # Remove empty entries
        if not self.request_history[client_ip]:
            del self.request_history[client_ip]
