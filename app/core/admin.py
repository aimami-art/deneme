"""
Admin Authorization Utilities
Admin kullanıcı kontrolü için yardımcı fonksiyonlar
"""

from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth_service import AuthService
from app.core.database import get_db

# Admin email adresi
ADMIN_EMAIL = "muhammeduygur594@hotmail.com"


def get_admin_user(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Admin kullanıcı kontrolü
    Sadece admin kullanıcı erişebilir
    """
    # Email kontrolü
    if current_user.email != ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    # is_admin flag'i kontrolü (varsa)
    if hasattr(current_user, 'is_admin') and not current_user.is_admin:
        # Admin email'i varsa otomatik olarak is_admin=True yap
        try:
            current_user.is_admin = True
            db.commit()
            db.refresh(current_user)
        except Exception:
            pass  # DB güncelleme hatası olursa devam et
    
    return current_user


def check_admin_email(email: str) -> bool:
    """Email adresinin admin olup olmadığını kontrol et"""
    return email.lower() == ADMIN_EMAIL.lower()


def get_admin_user_id(db: Session) -> int:
    """Admin kullanıcının ID'sini al"""
    try:
        admin_user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        return admin_user.id if admin_user else None
    except Exception:
        return None