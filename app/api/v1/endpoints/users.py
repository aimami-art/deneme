"""
Users API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth import UserResponse, UserUpdate, ChangePasswordRequest

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(AuthService.get_current_user)
):
    """Mevcut kullanıcı bilgilerini getir"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Kullanıcı bilgilerini güncelle"""
    # Email değişikliği kontrolü
    if user_data.email and user_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu e-posta adresi zaten kullanılıyor"
            )
    
    # Kullanıcı adı değişikliği kontrolü
    if user_data.username and user_data.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu kullanıcı adı zaten kullanılıyor"
            )
    
    # Şifre değişikliği
    if user_data.password:
        auth_service = AuthService(db)
        current_user.hashed_password = auth_service.get_password_hash(user_data.password)
    
    # Diğer alanları güncelle
    if user_data.email:
        current_user.email = user_data.email
    if user_data.username:
        current_user.username = user_data.username
    if user_data.full_name:
        current_user.full_name = user_data.full_name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Kullanıcı şifresini değiştir"""
    auth_service = AuthService(db)
    
    # Mevcut şifreyi doğrula
    if not auth_service.verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre yanlış"
        )
    
    # Yeni şifre uzunluk kontrolü
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre en az 6 karakter olmalıdır"
        )
    
    # Yeni şifreyi hashle ve kaydet
    current_user.hashed_password = auth_service.get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Şifre başarıyla değiştirildi"}


@router.delete("/delete-account")
async def delete_account(
    db: Session = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """Kullanıcı hesabını sil"""
    try:
        # Kullanıcıyı veritabanından sil
        db.delete(current_user)
        db.commit()
        
        return {"message": "Hesap başarıyla silindi"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hesap silinirken bir hata oluştu"
        ) 