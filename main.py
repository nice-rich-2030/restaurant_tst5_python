"""
Restaurant Search Web Application - Main Entry Point
FastAPI server with Google AI Grounding Search integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import get_settings, clear_settings_cache
from app.logger import logger
from app.routers import search

# Clear cache and reload settings from .env on startup
clear_settings_cache()
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Restaurant Search Web App",
    description="Google AI Grounding Search verification tool for restaurant searches",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 80)
    logger.info("Restaurant Search Web Application Starting")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("Restaurant Search Web Application Shutting Down")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "restaurant-search-api",
        "model": settings.gemini_model
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.host}:{settings.port}")

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
