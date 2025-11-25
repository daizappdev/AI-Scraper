from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.models import Base
from app.api import auth, scrapers, users, admin
from app.core.config import settings
from app.core.logging import setup_logging

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="AI-Scraper API",
    description="API for generating and executing web scraping scripts using AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(scrapers.router, prefix="/api/scrapers", tags=["scrapers"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AI-Scraper API"}

@app.get("/")
async def root():
    return {"message": "AI-Scraper API is running"}

@app.get("/api/v1")
async def api_info():
    return {
        "name": "AI-Scraper API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )