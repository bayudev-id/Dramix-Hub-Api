"""FastAPI application entry point."""
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.client.iqiyi_client import IQIYIClient
from src.models.schemas import StandardResponse
from production.api.routes_auth import router as auth_router
from production.api.routes_catalog import router as catalog_router
from production.api.routes_playback import router as playback_router

# Initialize app
app = FastAPI(
    title="iQIYI Catalog & Stream Playback API",
    description="FastAPI service exposing iQIYI catalog, authentication, and video stream playback with subtitles",
    version="2.0.0",
)

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client singleton
_client: IQIYIClient = None


def get_client() -> IQIYIClient:
    """Get or initialize singleton client."""
    global _client
    if _client is None:
        _client = IQIYIClient()
    return _client


@app.on_event("startup")
async def startup_event():
    """Initialize client on app startup."""
    get_client()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    global _client
    if _client is not None:
        if _client._http_client is not None:
            _client._http_client.close()
        _client = None


# Error handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": None,
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return StandardResponse[dict](
        code=200,
        message="OK",
        data={"status": "healthy"}
    )


# Include routers
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(playback_router)


# Root endpoint
@app.get("/")
async def root():
    """API root info."""
    return StandardResponse[dict](
        code=200,
        message="iQIYI API v2.0.0",
        data={"service": "iqiyi_api", "port": os.getenv("SERVER_PORT", 6107)}
    )
