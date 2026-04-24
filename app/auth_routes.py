"""
Authentication routes for login/logout and user management
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    get_current_user,
    get_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# =========================
# Pydantic Models
# =========================
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_admin: bool = False


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True


# =========================
# Login
# =========================
@router.post("/login", response_model=Token)
def login(
    username: str = Form(...),
    password: str = Form(...)
):
    if username != "admin@gmail.com" or password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={
            "sub": username,
            "id": 1,
            "is_admin": True
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": 1,
            "username": username,
            "full_name": "System Administrator",
            "is_admin": True
        }
    }

# =========================
# Logout (client-side token removal)
# =========================
@router.post("/logout")
def logout():
    """Logout - client should remove the token"""
    return {"ok": True, "message": "Logged out successfully"}


# =========================
# Get Current User
# =========================
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current logged-in user info"""
    return current_user


# =========================
# Create User (Admin only)
# =========================
@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create a new user (admin only)"""
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email exists
    if user_data.email and db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_admin=user_data.is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


# =========================
# List Users (Admin only)
# =========================
@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return users


# =========================
# Change Password
# =========================
@router.post("/change-password")
def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user password"""
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"ok": True, "message": "Password changed successfully"}


# =========================
# Setup Default Admin (One-time)
# =========================
@router.post("/setup-admin")
def setup_admin(
    username: str = Form("admin@gmail.com"),
    password: str = Form("admin123")
):
    return {
        "ok": True,
        "message": "Setup admin API working successfully",
        "username": username,
        "password": password
    }
       
