from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI-Scraper API"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]  # Configure properly in production
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_scraper.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.1
    
    # Script Execution
    SCRIPT_TIMEOUT: int = 300  # 5 minutes
    MAX_SCRIPT_SIZE: int = 10000  # characters
    SCRAPER_OUTPUT_DIR: str = "./outputs"
    SCRIPTS_DIR: str = "./generated_scripts"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".py", ".txt", ".json"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create global settings instance
settings = Settings()

# Override for development
if settings.DEBUG:
    settings.ALLOWED_HOSTS = ["*"]
else:
    # Production CORS settings
    settings.ALLOWED_HOSTS = [
        "localhost:3000",
        "localhost:5173",
        # Add your production domain
    ]