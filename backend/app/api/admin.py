from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Scraper, ExecutionLog, AIGenerationLog, SystemSettings
from app.api.auth import get_current_active_user
from pydantic import BaseModel

router = APIRouter()

# Require admin access for all admin endpoints
async def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Pydantic models
class AdminStats(BaseModel):
    total_users: int
    active_users: int
    premium_users: int
    total_scrapers: int
    active_scrapers: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    ai_generations_today: int
    ai_generations_this_month: int
    credits_in_circulation: int

class UserManagement(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_premium: bool
    credits: int
    created_at: str
    last_login: Optional[str] = None
    total_scrapers: int
    total_executions: int

    class Config:
        from_attributes = True

class SystemSettingsResponse(BaseModel):
    key: str
    value: str
    description: Optional[str]
    updated_at: str

    class Config:
        from_attributes = True

class SystemSettingsUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive system statistics"""
    
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    premium_users = db.query(User).filter(User.is_premium == True).count()
    
    # Scraper statistics
    total_scrapers = db.query(Scraper).count()
    active_scrapers = db.query(Scraper).filter(Scraper.status == "active").count()
    
    # Execution statistics
    total_executions = db.query(ExecutionLog).count()
    successful_executions = db.query(ExecutionLog).filter(
        ExecutionLog.status == "completed"
    ).count()
    failed_executions = db.query(ExecutionLog).filter(
        ExecutionLog.status.in_(["failed", "timeout"])
    ).count()
    
    # AI generation statistics
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ai_generations_today = db.query(AIGenerationLog).filter(
        AIGenerationLog.created_at >= today
    ).count()
    
    month_start = today.replace(day=1)
    ai_generations_this_month = db.query(AIGenerationLog).filter(
        AIGenerationLog.created_at >= month_start
    ).count()
    
    # Credits in circulation
    credits_in_circulation = db.query(func.sum(User.credits)).scalar() or 0
    
    return AdminStats(
        total_users=total_users,
        active_users=active_users,
        premium_users=premium_users,
        total_scrapers=total_scrapers,
        active_scrapers=active_scrapers,
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        ai_generations_today=ai_generations_today,
        ai_generations_this_month=ai_generations_this_month,
        credits_in_circulation=credits_in_circulation
    )

@router.get("/users", response_model=List[UserManagement])
async def get_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    active_only: bool = False,
    premium_only: bool = False,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user management data with optional filtering"""
    
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                User.email.contains(search),
                User.username.contains(search),
                User.full_name.contains(search)
            )
        )
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    if premium_only:
        query = query.filter(User.is_premium == True)
    
    # Get basic user data
    users = query.offset(skip).limit(limit).all()
    
    # Enhance with statistics
    enhanced_users = []
    for user in users:
        total_scrapers = db.query(func.count(Scraper.id)).filter(
            Scraper.user_id == user.id
        ).scalar()
        
        total_executions = db.query(func.count(ExecutionLog.id)).filter(
            ExecutionLog.user_id == user.id
        ).scalar()
        
        user_management = UserManagement(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_premium=user.is_premium,
            credits=user.credits,
            created_at=user.created_at.isoformat(),
            last_login=None,  # You could track this
            total_scrapers=total_scrapers,
            total_executions=total_executions
        )
        enhanced_users.append(user_management)
    
    return enhanced_users

@router.get("/users/{user_id}", response_model=UserManagement)
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    total_scrapers = db.query(func.count(Scraper.id)).filter(
        Scraper.user_id == user.id
    ).scalar()
    
    total_executions = db.query(func.count(ExecutionLog.id)).filter(
        ExecutionLog.user_id == user.id
    ).scalar()
    
    return UserManagement(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_premium=user.is_premium,
        credits=user.credits,
        created_at=user.created_at.isoformat(),
        last_login=None,
        total_scrapers=total_scrapers,
        total_executions=total_executions
    )

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Activate/deactivate a user account"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    db.commit()
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully"}

@router.put("/users/{user_id}/premium")
async def update_user_premium_status(
    user_id: int,
    is_premium: bool,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user's premium status"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_premium = is_premium
    db.commit()
    
    return {"message": f"User premium status {'enabled' if is_premium else 'disabled'} successfully"}

@router.put("/users/{user_id}/credits")
async def update_user_credits(
    user_id: int,
    credits: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user's credit balance"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.credits = credits
    db.commit()
    
    return {"message": f"User credits updated to {credits}"}

@router.get("/executions/recent", response_model=List[dict])
async def get_recent_executions(
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent execution logs"""
    
    query = db.query(ExecutionLog).join(User).join(Scraper)
    
    if status_filter:
        query = query.filter(ExecutionLog.status == status_filter)
    
    executions = query.order_by(desc(ExecutionLog.created_at)).limit(limit).all()
    
    result = []
    for execution in executions:
        result.append({
            "id": execution.id,
            "username": execution.user.username,
            "scraper_name": execution.scraper.name,
            "status": execution.status,
            "input_url": execution.input_url,
            "execution_time": execution.execution_time,
            "created_at": execution.created_at.isoformat(),
            "error_message": execution.error_message
        })
    
    return result

@router.get("/ai-logs/recent")
async def get_recent_ai_logs(
    limit: int = 20,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent AI generation logs"""
    
    logs = db.query(AIGenerationLog).join(User).order_by(
        desc(AIGenerationLog.created_at)
    ).limit(limit).all()
    
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "username": log.user.username,
            "ai_model_used": log.ai_model_used,
            "tokens_used": log.tokens_used,
            "cost": log.cost,
            "success": log.success,
            "created_at": log.created_at.isoformat(),
            "error_message": log.error_message
        })
    
    return result

@router.get("/settings", response_model=List[SystemSettingsResponse])
async def get_system_settings(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all system settings"""
    
    settings = db.query(SystemSettings).all()
    return settings

@router.put("/settings", response_model=SystemSettingsResponse)
async def update_system_setting(
    setting_data: SystemSettingsUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a system setting"""
    
    setting = db.query(SystemSettings).filter(
        SystemSettings.key == setting_data.key
    ).first()
    
    if setting:
        setting.value = setting_data.value
        if setting_data.description:
            setting.description = setting_data.description
    else:
        setting = SystemSettings(
            key=setting_data.key,
            value=setting_data.value,
            description=setting_data.description
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    
    return setting

@router.get("/system/health")
async def system_health_check(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """System health monitoring"""
    
    health_data = {
        "database": "healthy",
        "ai_service": "available" if settings.OPENAI_API_KEY else "unavailable",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Test database connection
    try:
        db.execute("SELECT 1")
    except Exception as e:
        health_data["database"] = f"unhealthy: {str(e)}"
    
    return health_data