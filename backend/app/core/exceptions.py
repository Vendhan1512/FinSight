import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

class FinSightException(Exception):
    """Base exception for all FinSight custom errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(FinSightException)
    async def finsight_exception_handler(request: Request, exc: FinSightException):
        logger.error(f"FinSightException: {exc.message} at {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_type": "FinSightException"},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTPException: {exc.detail} at {request.url} (status={exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled Exception at {request.url}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
