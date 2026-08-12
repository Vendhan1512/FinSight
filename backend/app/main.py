from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.middleware import RequestIDMiddleware, RateLimitMiddleware

from app.api import health
from app.api.v1 import auth, intelligence, system

# Setup structured logging
logger = setup_logging()

app = FastAPI(title=settings.app_name, version="1.0.0")

# Middlewares (Order matters! RequestID first, then RateLimit, then CORS)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup centralized exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.app_name} API v1"}
