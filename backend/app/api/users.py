from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User, Scraper, ExecutionLog
from app.api.auth import get_current_active_user
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Pydantic models
class UserStats(BaseModel):
    total_scrapers: int
    active_scrapers: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    credits_remaining: int
    usage_this_month: int

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_premium: bool
    credits: int
    created_at: str
    stats: UserStats

    class Config:
        from_attributes = True

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed user profile with statistics"""
    
    # Calculate statistics
    total_scrapers = db.query(Scraper).filter(Scraper.user_id == current_user.id).count()
    active_scrapers = db.query(Scraper).filter(
        Scraper.user_id == current_user.id,
        Scraper.status == "active"
    ).count()
    
    total_executions = db.query(ExecutionLog).filter(
        ExecutionLog.user_id == current_user.id
    ).count()
    
    successful_executions = db.query(ExecutionLog).filter(
        ExecutionLog.user_id == current_user.id,
        ExecutionLog.status == "completed"
    ).count()
    
    failed_executions = db.query(ExecutionLog).filter(
        ExecutionLog.user_id == current_user.id,
        ExecutionLog.status.in_(["failed", "timeout"])
    ).count()
    
    # Get usage this month (simplified - you might want to use proper date filtering)
    from datetime import datetime
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_this_month = db.query(ExecutionLog).filter(
        ExecutionLog.user_id == current_user.id,
        ExecutionLog.created_at >= current_month
    ).count()
    
    stats = UserStats(
        total_scrapers=total_scrapers,
        active_scrapers=active_scrapers,
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        credits_remaining=current_user.credits,
        usage_this_month=usage_this_month
    )
    
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_premium=current_user.is_premium,
        credits=current_user.credits,
        created_at=current_user.created_at.isoformat(),
        stats=stats
    )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    # Check if email is already taken by another user
    if profile_update.email and profile_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == profile_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user"
            )
        current_user.email = profile_update.email
    
    # Update other fields
    if profile_update.full_name is not None:
        current_user.full_name = profile_update.full_name
    
    db.commit()
    db.refresh(current_user)
    
    # Return updated profile with stats
    return await get_user_profile(current_user, db)

@router.get("/credits")
async def get_user_credits(current_user: User = Depends(get_current_active_user)):
    """Get user credit balance"""
    return {"credits": current_user.credits}

@router.post("/credits/consume")
async def consume_credits(
    amount: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Consume user credits (e.g., for AI generation)"""
    
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    if current_user.credits < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient credits",
            headers={"X-Insufficient-Credits": "true"}
        )
    
    current_user.credits -= amount
    db.commit()
    
    return {"credits": current_user.credits, "consumed": amount}

@router.post("/credits/add")
async def add_credits(
    amount: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add credits to user account (admin function or premium upgrade)"""
    
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    current_user.credits += amount
    db.commit()
    
    return {"credits": current_user.credits, "added": amount}

@router.get("/scrapers")
async def get_user_scrapers(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's scrapers"""
    
    scrapers = db.query(Scraper).filter(
        Scraper.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return scrapers

@router.get("/executions")
async def get_user_executions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's execution history"""
    
    executions = db.query(ExecutionLog).filter(
        ExecutionLog.user_id == current_user.id
    ).order_by(ExecutionLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return executions

@router.delete("/account")
async def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data"""
    
    try:
        # Delete all user data
        db.delete(current_user)
        db.commit()
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )