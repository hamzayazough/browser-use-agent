from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from app.api.content_packs import router as content_packs_router
from app.api.logs import router as logs_router
from app.database import connect_to_mongo, close_mongo_connection

# Initialize FastAPI app
app = FastAPI(
    title="Curriculum Discovery API",
    description="Automated curriculum + materials pack builder using Browser-Use agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()

# Include routers
app.include_router(content_packs_router)
app.include_router(logs_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Curriculum Discovery API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "openai_configured": bool(settings.openai_api_key),
        "browser_use_configured": bool(settings.browser_use_api_key),
        "mongodb_configured": bool(settings.mongodb_uri),
        "vector_db_provider": settings.vector_db_provider,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.reload,
        log_level=settings.log_level,
    )
