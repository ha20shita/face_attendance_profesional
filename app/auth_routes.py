"""
Authentication routes for login/logout and user management
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
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
    name: str
    email: Optional[str]
    phone: Optional[str]
    role: str

    class Config:
        from_attributes = True


# =========================
# Login - DB se verify karo
# =========================
@router.post("/login", response_model=Token)
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Email se user dhundho
    user = db.query(User).filter(User.email == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Hashed password verify karo
    if password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "is_admin": user.role == "admin"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.email,
            "full_name": user.name or "Administrator",
            "is_admin": user.role == "admin"
        }
    }

# =========================
# Logout
# =========================
@router.post("/logout")
def logout():
    return {"ok": True, "message": "Logged out successfully"}


# =========================
# Get Current User
# =========================
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# =========================
# Create User (Admin only)
# =========================
#@router.post("/users", response_model=UserResponse)
#def create_user(
  #  user_data: UserCreate,
 #   db: Session = Depends(get_db),
   # admin: User = Depends(get_admin_user)
#):
   # if db.query(User).filter(User.username == user_data.username).first():
    #    raise HTTPException(
      #      status_code=status.HTTP_400_BAD_REQUEST,
       #     detail="Username already exists"
       # )

   # if user_data.email and db.query(User).filter(User.email == user_data.email).first():
      #  raise HTTPException(
       #     status_code=status.HTTP_400_BAD_REQUEST,
      #      detail="Email already exists"
      #  )

   # new_user = User(
    #    username=user_data.username,
    #    email=user_data.email,
    #    hashed_password=get_password_hash(user_data.password),
    #    full_name=user_data.full_name,
   #     is_admin=user_data.is_admin
   # )

   # db.add(new_user)
    #db.commit()
   # db.refresh(new_user)
   # return new_user


# =========================
# List Users (Admin only)
# =========================
@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    return db.query(User).all()


# =========================
# Change Password
# =========================
#@router.post("/change-password")
#def change_password(
  #  old_password: str = Form(...),
  #  new_password: str = Form(...),
  #  db: Session = Depends(get_db),
 #   current_user: User = Depends(get_current_user)
#):
  #  if not verify_password(old_password, current_user.hashed_password):
    #    raise HTTPException(
        #    status_code=status.HTTP_400_BAD_REQUEST,
         #   detail="Old password is incorrect"
       # )

  #  current_user.hashed_password = get_password_hash(new_password)
 #   db.commit()
  #  return {"ok": True, "message": "Password changed successfully"}


# =========================
# Setup Admin - Pehli baar admin banao
# =========================
@router.get("/setup-admin")
def setup_admin(
    username: str = "admin@gmail.com",
    password: str = "admin123",
    db: Session = Depends(get_db)
):
    # Check karo admin pehle se hai ya nahi
    existing = db.query(User).filter(User.email == username).first()
    if existing:
        return {
            "ok": True,
            "message": "Admin already exists",
            "username": username
        }

    # Naya admin banao
    admin_user = User(
    name="Adminschool",
    email=username,
    password=password,
    phone="",
    role="admin"
)

    db.add(admin_user)
    db.commit()

    return {
        "ok": True,
        "message": "Admin created successfully",
        "username": username
    }
