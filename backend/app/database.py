from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle SQLite for development and PostgreSQL for production
if "postgresql" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.DEBUG
    )
    logger.info("Using PostgreSQL database")
else:
    # SQLite configuration for development
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
        echo=settings.DEBUG
    )
    logger.info("Using SQLite database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def drop_tables():
    """Drop all database tables (for development/testing)"""
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")