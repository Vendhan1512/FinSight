from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.api import health

# Setup structured logging
logger = setup_logging()

app = FastAPI(title=settings.app_name)

# Allow CORS for the frontend
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

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.app_name}"}
