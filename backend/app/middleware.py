import time
import uuid
import logging
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(f"[{request_id}] {request.method} {request.url.path} - {response.status_code}")
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiter using a sliding window.
    WARNING: Only suitable for single-worker or sticky-session deployments.
    Not for distributed multi-pod scale without an external store like Redis.
    """
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        # Exclude health endpoints from rate limiting
        if request.url.path.startswith("/health"):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean old history
        self.history[client_ip] = [ts for ts in self.history[client_ip] if now - ts < self.window_seconds]
        
        if len(self.history[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error_code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please try again later.", "request_id": getattr(request.state, "request_id", "unknown")}
            )
            
        self.history[client_ip].append(now)
        
        return await call_next(request)
