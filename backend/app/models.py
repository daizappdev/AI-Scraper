from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    credits = Column(Integer, default=100)  # AI generation credits
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    scrapers = relationship("Scraper", back_populates="user", cascade="all, delete-orphan")
    executions = relationship("ExecutionLog", back_populates="user", cascade="all, delete-orphan")

class ScraperStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

class Scraper(Base):
    __tablename__ = "scrapers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    target_url = Column(String(2048), nullable=False)
    fields_to_scrape = Column(JSON, nullable=False)  # List of field definitions
    generated_script = Column(Text, nullable=True)  # Generated Python code
    status = Column(Enum(ScraperStatus), default=ScraperStatus.DRAFT)
    is_public = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # List of tags
    usage_count = Column(Integer, default=0)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scrapers")
    executions = relationship("ExecutionLog", back_populates="scraper", cascade="all, delete-orphan")

class ExecutionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scraper_id = Column(Integer, ForeignKey("scrapers.id"), nullable=False)
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    input_url = Column(String(2048), nullable=False)
    output_format = Column(String(20), default="json")  # json, csv, xml
    output_data = Column(Text, nullable=True)  # Generated data
    output_file_path = Column(String(500), nullable=True)  # Path to output file
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="executions")
    scraper = relationship("Scraper", back_populates="executions")

class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scraper_id = Column(Integer, ForeignKey("scrapers.id"), nullable=True)
    prompt = Column(Text, nullable=False)  # User's request to AI
    generated_script = Column(Text, nullable=False)  # AI response
    ai_model_used = Column(String(50), nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())