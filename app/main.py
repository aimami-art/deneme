"""
AI Satış Stratejisi Projesi - Ana Uygulama
FastAPI tabanlı backend servisi
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1 import api_router
from app.core.database import init_db
from app.services.agent_orchestrator import agent_orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıç ve kapanış olayları"""
    # Başlangıç
    print("🚀 AI Satış Stratejisi Projesi başlatılıyor...")
    await init_db()
    print("✅ Veritabanı bağlantısı kuruldu")
    
    # Agent Orchestrator'ı başlat
    try:
        await agent_orchestrator.start()
        print("🤖 Agent Orchestrator başlatıldı")
    except Exception as e:
        print(f"⚠️ Agent Orchestrator başlatılamadı: {e}")
    
    yield
    
    # Kapanış
    print("🔄 Uygulama kapatılıyor...")
    
    # Agent Orchestrator'ı durdur
    try:
        await agent_orchestrator.stop()
        print("🛑 Agent Orchestrator durduruldu")
    except Exception as e:
        print(f"⚠️ Agent Orchestrator durdurulamadı: {e}")


# FastAPI uygulaması
app = FastAPI(
    title="AI Satış Stratejisi Projesi",
    description="Yapay zeka destekli satış stratejisi geliştirme platformu",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dosyalar
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    """Ana sayfa"""
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard sayfası"""
    with open("app/templates/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/create-strategy", response_class=HTMLResponse)
async def create_strategy():
    """Strateji oluşturma sayfası"""
    with open("app/templates/create_strategy.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/view-strategy", response_class=HTMLResponse)
async def view_strategy():
    """Strateji görüntüleme sayfası"""
    with open("app/templates/view_strategy.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/performance", response_class=HTMLResponse)
async def performance():
    """Performans takibi sayfası"""
    with open("app/templates/performance.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/settings", response_class=HTMLResponse)
async def settings():
    """Ayarlar sayfası"""
    with open("app/templates/settings.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    return {
        "status": "healthy",
        "service": "AI Satış Stratejisi API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 