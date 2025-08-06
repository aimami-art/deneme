"""
Veritabanı Konfigürasyonu ve Session Yönetimi
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from typing import Generator

from app.core.config import settings

# PostgreSQL Engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=settings.DEBUG,
    connect_args={
        "options": "-c timezone=Europe/Istanbul"
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_db() -> Generator[Session, None, None]:
    """Veritabanı session dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_redis():
    """Redis client dependency"""
    return redis_client


async def init_db():
    """Veritabanı başlatma"""
    try:
        # Tabloları oluştur
        Base.metadata.create_all(bind=engine)
        print("✅ Veritabanı tabloları oluşturuldu")
        
        # Redis bağlantısını test et
        redis_client.ping()
        print("✅ Redis bağlantısı başarılı")
        
    except Exception as e:
        print(f"❌ Veritabanı başlatma hatası: {e}")
        raise e 