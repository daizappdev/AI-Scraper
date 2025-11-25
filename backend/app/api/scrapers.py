from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import shutil
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, Scraper, ScraperStatus, ExecutionLog, ExecutionStatus, AIGenerationLog
from app.api.auth import get_current_active_user
from app.ai_agent import AIScraperAgent
from app.core.config import settings
from pydantic import BaseModel, HttpUrl
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
ai_agent = AIScraperAgent()

# Pydantic models
class ScraperField(BaseModel):
    name: str
    description: str
    selector: Optional[str] = None
    required: bool = False

class ScraperCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_url: HttpUrl
    fields_to_scrape: List[ScraperField]
    tags: Optional[List[str]] = None
    is_public: bool = False

class ScraperUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_url: Optional[HttpUrl] = None
    fields_to_scrape: Optional[List[ScraperField]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None

class ScraperGenerate(BaseModel):
    description: Optional[str] = None

class ScraperResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_url: str
    fields_to_scrape: List[dict]
    status: str
    is_public: bool
    tags: Optional[List[str]]
    usage_count: int
    last_run_at: Optional[str]
    created_at: str
    updated_at: str
    generated_script: Optional[str] = None

    class Config:
        from_attributes = True

class ExecutionRequest(BaseModel):
    output_format: str = "json"  # json, csv, xml
    custom_url: Optional[HttpUrl] = None

class ExecutionResponse(BaseModel):
    id: int
    status: str
    input_url: str
    output_format: str
    output_file_path: Optional[str]
    error_message: Optional[str]
    execution_time: Optional[int]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=ScraperResponse)
async def create_scraper(
    scraper_data: ScraperCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new scraper"""
    
    # Validate URL is reachable (basic check)
    if not scraper_data.target_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must start with http:// or https://"
        )
    
    # Create scraper
    scraper = Scraper(
        user_id=current_user.id,
        name=scraper_data.name,
        description=scraper_data.description,
        target_url=str(scraper_data.target_url),
        fields_to_scrape=[field.dict() for field in scraper_data.fields_to_scrape],
        tags=scraper_data.tags,
        is_public=scraper_data.is_public,
        status=ScraperStatus.DRAFT
    )
    
    db.add(scraper)
    db.commit()
    db.refresh(scraper)
    
    return scraper

@router.get("/", response_model=List[ScraperResponse])
async def get_scrapers(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's scrapers"""
    
    query = db.query(Scraper).filter(Scraper.user_id == current_user.id)
    
    if status_filter:
        try:
            status_enum = ScraperStatus(status_filter)
            query = query.filter(Scraper.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}"
            )
    
    scrapers = query.offset(skip).limit(limit).all()
    
    # For security, only return generated_script for user's own scrapers
    return scrapers

@router.get("/{scraper_id}", response_model=ScraperResponse)
async def get_scraper(
    scraper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific scraper"""
    
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    return scraper

@router.put("/{scraper_id}", response_model=ScraperResponse)
async def update_scraper(
    scraper_id: int,
    scraper_update: ScraperUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a scraper"""
    
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    # Update fields
    update_data = scraper_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "fields_to_scrape":
            scraper.fields_to_scrape = [field.dict() for field in value]
        elif field == "status":
            try:
                scraper.status = ScraperStatus(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {value}"
                )
        elif hasattr(scraper, field):
            setattr(scraper, field, value)
    
    db.commit()
    db.refresh(scraper)
    
    return scraper

@router.delete("/{scraper_id}")
async def delete_scraper(
    scraper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a scraper"""
    
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    db.delete(scraper)
    db.commit()
    
    return {"message": "Scraper deleted successfully"}

@router.post("/{scraper_id}/generate", response_model=ScraperResponse)
async def generate_scraper_script(
    scraper_id: int,
    generation_request: ScraperGenerate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate AI script for a scraper"""
    
    # Check if user has enough credits
    AI_GENERATION_COST = 10  # Cost per generation
    if current_user.credits < AI_GENERATION_COST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient credits for AI generation",
            headers={"X-Insufficient-Credits": "true"}
        )
    
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    try:
        # Extract fields for AI prompt
        fields = [field["name"] for field in scraper.fields_to_scrape]
        
        # Generate script using AI
        script_content, usage = await ai_agent.generate_scraper_script(
            url=str(scraper.target_url),
            fields=fields,
            description=generation_request.description,
            user_id=current_user.id,
            db=db
        )
        
        # Validate generated script
        is_valid, issues = ai_agent.validate_script(script_content)
        if not is_valid:
            logger.warning(f"Script validation issues: {issues}")
            # Continue anyway, but log the issues
        
        # Update scraper with generated script
        scraper.generated_script = script_content
        scraper.status = ScraperStatus.ACTIVE
        
        # Consume credits
        current_user.credits -= AI_GENERATION_COST
        
        db.commit()
        db.refresh(scraper)
        
        logger.info(f"Generated script for scraper {scraper_id} using {usage.get('model', 'unknown')} model")
        
        return scraper
        
    except Exception as e:
        logger.error(f"Failed to generate script for scraper {scraper_id}: {e}")
        
        # Log failed generation attempt
        try:
            log_entry = AIGenerationLog(
                user_id=current_user.id,
                scraper_id=scraper_id,
                prompt="Script generation failed",
                generated_script="",
                ai_model_used="failed",
                tokens_used=0,
                cost=0.0,
                success=False,
                error_message=str(e)
            )
            db.add(log_entry)
            db.commit()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate script: {str(e)}"
        )

@router.get("/{scraper_id}/script")
async def download_scraper_script(
    scraper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download generated script as file"""
    
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    if not scraper.generated_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No generated script found. Generate a script first."
        )
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    script_filename = f"scraper_{scraper_id}_{uuid.uuid4().hex[:8]}.py"
    script_path = os.path.join(temp_dir, script_filename)
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(scraper.generated_script)
        
        return FileResponse(
            path=script_path,
            filename=script_filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        # Clean up temp file
        if os.path.exists(script_path):
            os.remove(script_path)
        shutil.rmtree(temp_dir)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create script file: {str(e)}"
        )

@router.post("/{scraper_id}/execute", response_model=ExecutionResponse)
async def execute_scraper(
    scraper_id: int,
    execution_request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute a scraper in the background"""
    
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    if not scraper.generated_script:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generated script available. Generate a script first."
        )
    
    # Create execution record
    execution = ExecutionLog(
        user_id=current_user.id,
        scraper_id=scraper_id,
        input_url=str(execution_request.custom_url or scraper.target_url),
        output_format=execution_request.output_format,
        status=ExecutionStatus.PENDING
    )
    
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Execute in background
    background_tasks.add_task(
        execute_scraper_background,
        execution.id,
        scraper_id,
        str(execution_request.custom_url or scraper.target_url),
        execution_request.output_format
    )
    
    # Update scraper usage count
    scraper.usage_count += 1
    scraper.last_run_at = datetime.utcnow()
    db.commit()
    
    return execution

@router.get("/{scraper_id}/executions", response_model=List[ExecutionResponse])
async def get_scraper_executions(
    scraper_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get execution history for a scraper"""
    
    # Verify scraper belongs to user
    scraper = db.query(Scraper).filter(
        Scraper.id == scraper_id,
        Scraper.user_id == current_user.id
    ).first()
    
    if not scraper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper not found"
        )
    
    executions = db.query(ExecutionLog).filter(
        ExecutionLog.scraper_id == scraper_id,
        ExecutionLog.user_id == current_user.id
    ).order_by(ExecutionLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return executions

async def execute_scraper_background(
    execution_id: int,
    scraper_id: int,
    url: str,
    output_format: str
):
    """Background task to execute scraper script"""
    # This is a placeholder for the actual script execution
    # In a real implementation, you would:
    # 1. Create a temporary Python script
    # 2. Execute it in a sandboxed environment
    # 3. Capture output and errors
    # 4. Update the execution record
    
    logger.info(f"Background execution started for execution {execution_id}")
    
    try:
        # Update status to running
        db = next(get_db())
        execution = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        db.commit()
        
        # Placeholder: Simulate script execution
        await asyncio.sleep(5)  # Simulate execution time
        
        # For now, just mark as completed with mock data
        execution.status = ExecutionStatus.COMPLETED
        execution.output_data = '[{"name": "Test Data", "value": "Example"}]'
        execution.completed_at = datetime.utcnow()
        execution.execution_time = 5
        
        db.commit()
        
        logger.info(f"Background execution completed for execution {execution_id}")
        
    except Exception as e:
        logger.error(f"Background execution failed for execution {execution_id}: {e}")
        
        # Update execution with error
        execution = db.query(ExecutionLog).filter(ExecutionLog.id == execution_id).first()
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        execution.completed_at = datetime.utcnow()
        db.commit()
    
    finally:
        db.close()