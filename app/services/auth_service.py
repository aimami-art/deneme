"""
Authentication Service
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class AuthService:
    """Authentication business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Şifre doğrulama"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Şifre hash'leme"""
        return pwd_context.hash(password)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Kullanıcı adına göre kullanıcı getir"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """E-posta'ya göre kullanıcı getir"""
        return self.db.query(User).filter(User.email == email).first()
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Kullanıcı kimlik doğrulama"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Yeni kullanıcı oluştur"""
        # Kullanıcı adı kontrolü
        if self.get_user_by_username(user_data.username):
            raise ValueError("Bu kullanıcı adı zaten kullanılıyor")
        
        # E-posta kontrolü
        if self.get_user_by_email(user_data.email):
            raise ValueError("Bu e-posta adresi zaten kullanılıyor")
        
        # Yeni kullanıcı oluştur
        hashed_password = self.get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """JWT token oluştur"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Mevcut kullanıcıyı token'dan getir"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        
        auth_service = AuthService(db)
        user = auth_service.get_user_by_username(username=token_data.username)
        if user is None:
            raise credentials_exception
        
        return user 