"""
Authentication Schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Kullanıcı temel şeması"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Kullanıcı oluşturma şeması"""
    password: str


class UserUpdate(BaseModel):
    """Kullanıcı güncelleme şeması"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """Kullanıcı yanıt şeması"""
    id: int
    is_active: bool
    is_admin: Optional[bool] = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token şeması"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token veri şeması"""
    username: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Şifre değiştirme isteği şeması"""
    current_password: str
    new_password: str 