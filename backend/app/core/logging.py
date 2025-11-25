import logging
import logging.handlers
import os
from app.core.config import settings

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if not settings.DEBUG else logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")

# Create logger instances for different components
api_logger = logging.getLogger("api")
scraper_logger = logging.getLogger("scraper")
ai_logger = logging.getLogger("ai")
execution_logger = logging.getLogger("execution")