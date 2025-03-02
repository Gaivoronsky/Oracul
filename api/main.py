"""
Main entry point for the News Aggregator API.
Initializes and runs the FastAPI application.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv('LOG_DIR', 'logs'), 'api.log'))
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="News Aggregator API",
    description="API for accessing and searching news articles",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from api.routes.news import router as news_router
from api.routes.search import router as search_router
from api.routes.admin import router as admin_router

# Import middlewares
from api.middlewares.auth import AuthMiddleware
from api.middlewares.rate_limit import RateLimitMiddleware

# Add middlewares
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(news_router, prefix="/api/news", tags=["news"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.
    Returns basic API information.
    """
    return {
        "name": "News Aggregator API",
        "version": "1.0.0",
        "description": "API for accessing and searching news articles",
        "documentation": "/docs"
    }


@app.get("/health", tags=["health"])
async def health():
    """
    Health check endpoint.
    Returns the health status of the API.
    """
    # Check database connection
    db_status = "ok"
    try:
        from storage.database.repository import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    # Check Elasticsearch connection
    es_status = "ok"
    try:
        from storage.search.elasticsearch import get_elasticsearch_client
        es = get_elasticsearch_client()
        es.info()
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        es_status = "error"
    
    # Return health status
    return {
        "status": "ok" if db_status == "ok" and es_status == "ok" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "elasticsearch": es_status,
            "api": "ok"
        }
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "code": 500
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all requests.
    """
    start_time = datetime.now()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.2f}ms"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


def start():
    """
    Start the API server.
    """
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "False").lower() == "true"
    
    # Start server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start()