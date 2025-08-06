"""
Strateji yönetimi API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.strategy import Strategy
from app.models.product import Product
from app.schemas.strategy import StrategyCreate, StrategyResponse
from app.services.auth_service import AuthService
from app.models.user import User
from app.services.ai_services import StrategyBuilder

router = APIRouter()

# AI Strateji Builder instance
strategy_builder = StrategyBuilder()

# RAG Engine import (lazy loading için)
def get_rag_engine():
    try:
        from app.services.rag_engine import RAGEmbeddingEngine
        return RAGEmbeddingEngine()
    except ImportError:
        print("⚠️ RAG Engine import edilemedi")
        return None


async def add_strategy_to_vector_db_background(strategy_id: int, product_id: int):
    """Background task: Stratejiyi vector DB'ye ekle"""
    try:
        # Fresh session oluştur
        from app.core.database import get_db
        db: Session = next(get_db())
        
        try:
            # Strategy ve Product'ı fresh session'da tekrar yükle
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not strategy or not product:
                print(f"❌ Background: Strategy ({strategy_id}) veya Product ({product_id}) bulunamadı")
                return
                
            rag_engine = get_rag_engine()
            if rag_engine:
                success = await rag_engine.add_strategy_to_vector_db(strategy, product, db)
                if success:
                    print(f"✅ Background: Strateji vector DB'ye eklendi: {strategy.title}")
                else:
                    print(f"❌ Background: Strateji vector DB'ye eklenemedi: {strategy.title}")
            else:
                print("⚠️ Background: RAG Engine mevcut değil")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Background vector DB ekleme hatası: {e}")


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Yeni strateji oluştur (AI ile veya hazır içerikle)"""
    
    # Ürünün varlığını ve kullanıcıya ait olduğunu kontrol et
    product = db.query(Product).filter(
        Product.id == strategy_data.product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı veya size ait değil"
        )
    
    try:
        # Eğer strateji içeriği zaten varsa (frontend'den gelen), AI analizi yapma
        if strategy_data.content and strategy_data.content.strip():
            print(f"📄 Hazır strateji kaydediliyor: {product.name}")
            
            # Doğrudan kaydet
            db_strategy = Strategy(
                title=strategy_data.title or f"{product.name} Satış Stratejisi",
                content=strategy_data.content,
                product_id=product.id,
                user_id=current_user.id,
                confidence_score=strategy_data.confidence_score or 0.8,
                expected_roi=strategy_data.expected_roi or 0.2,
                implementation_difficulty=strategy_data.implementation_difficulty or "medium"
            )
        else:
            # İçerik yoksa AI ile oluştur
            print(f"🤖 AI strateji oluşturma başlatılıyor: {product.name}")
            ai_strategy_result = await strategy_builder.build_comprehensive_strategy(product)
            
            # Veritabanına kaydet
            db_strategy = Strategy(
                title=strategy_data.title or f"{product.name} Satış Stratejisi",
                content=ai_strategy_result.get("strategy_content", ""),
                product_id=product.id,
                user_id=current_user.id,
                confidence_score=ai_strategy_result.get("confidence_score", 0.8),
                expected_roi=ai_strategy_result.get("expected_roi", 0.2),
                implementation_difficulty=ai_strategy_result.get("implementation_difficulty", "medium"),
                analysis_data={
                    "market_analysis": ai_strategy_result.get("market_analysis", {}),
                    "audience_analysis": ai_strategy_result.get("audience_analysis", {}),
                    "pricing_analysis": ai_strategy_result.get("pricing_analysis", {}),
                    "messaging_analysis": ai_strategy_result.get("messaging_analysis", {})
                }
            )
        
        db.add(db_strategy)
        db.commit()
        db.refresh(db_strategy)
        
        print(f"✅ Strateji başarıyla oluşturuldu: ID {db_strategy.id}")
        
        # Background task: Vector DB'ye ekle
        background_tasks.add_task(
            add_strategy_to_vector_db_background,
            db_strategy.id,
            product.id
        )
        
        return db_strategy
        
    except Exception as e:
        print(f"❌ Strateji oluşturma hatası: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strateji oluşturulurken hata oluştu: {str(e)}"
        )


@router.get("/", response_model=List[StrategyResponse])
def get_strategies(
    skip: int = 0,
    limit: int = 100,
    product_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Kullanıcının stratejilerini listele (opsiyonel olarak ürüne göre filtrele)"""
    query = db.query(Strategy).filter(Strategy.user_id == current_user.id)
    
    # Eğer ürün ID'si belirtilmişse, ona göre filtrele
    if product_id:
        query = query.filter(Strategy.product_id == product_id)
    
    strategies = query.offset(skip).limit(limit).all()
    
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Belirli bir stratejiyi getir"""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strateji bulunamadı"
        )
    
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Stratejiyi güncelle"""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strateji bulunamadı"
        )
    
    # Ürün bilgisini al
    product = db.query(Product).filter(Product.id == strategy.product_id).first()
    
    # Güncelleme
    for field, value in strategy_data.dict(exclude_unset=True).items():
        setattr(strategy, field, value)
    
    db.commit()
    db.refresh(strategy)
    
    # Background task: Vector DB'yi güncelle
    if product:
        background_tasks.add_task(
            update_strategy_in_vector_db_background,
            strategy,
            product,
            db
        )
    
    return strategy


async def update_strategy_in_vector_db_background(strategy: Strategy, product: Product, db: Session):
    """Background task: Stratejiyi vector DB'de güncelle"""
    try:
        rag_engine = get_rag_engine()
        if rag_engine:
            success = await rag_engine.update_strategy_in_vector_db(strategy, product, db)
            if success:
                print(f"✅ Background: Strateji vector DB'de güncellendi: {strategy.title}")
            else:
                print(f"❌ Background: Strateji vector DB'de güncellenemedi: {strategy.title}")
    except Exception as e:
        print(f"❌ Background vector DB güncelleme hatası: {e}")


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Stratejiyi sil"""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strateji bulunamadı"
        )
    
    # Background task: Vector DB'den sil
    background_tasks.add_task(
        delete_strategy_from_vector_db_background,
        strategy_id
    )
    
    db.delete(strategy)
    db.commit()
    
    return {"message": "Strateji başarıyla silindi"}


async def delete_strategy_from_vector_db_background(strategy_id: int):
    """Background task: Stratejiyi vector DB'den sil"""
    try:
        rag_engine = get_rag_engine()
        if rag_engine:
            success = await rag_engine.delete_strategy_from_vector_db(strategy_id)
            if success:
                print(f"✅ Background: Strateji vector DB'den silindi: ID {strategy_id}")
            else:
                print(f"❌ Background: Strateji vector DB'den silinemedi: ID {strategy_id}")
    except Exception as e:
        print(f"❌ Background vector DB silme hatası: {e}")


@router.post("/analyze/{product_id}")
async def analyze_product_realtime(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Ürün için gerçek zamanlı AI analizi (strateji kaydetmeden)"""
    
    # Ürünün varlığını kontrol et
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    try:
        # AI analizi yap (kaydetme)
        print(f"🔍 Gerçek zamanlı analiz başlatılıyor: {product.name}")
        analysis_result = await strategy_builder.build_comprehensive_strategy(product)
        
        print(f"✅ Analiz tamamlandı: {product.name}")
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "analysis_result": analysis_result,
            "message": "Analiz başarıyla tamamlandı"
        }
        
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analiz yapılırken hata oluştu: {str(e)}"
        )


@router.post("/analyze/{product_id}/market")
async def analyze_market_only(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Sadece pazar analizi yap"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    try:
        print(f"📊 Pazar analizi başlatılıyor: {product.name}")
        market_result = await strategy_builder.analyze_market_only(product)
        print(f"✅ Pazar analizi tamamlandı: {product.name}")
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "analysis_type": "market",
            "result": market_result,
            "message": "Pazar analizi tamamlandı"
        }
        
    except Exception as e:
        print(f"❌ Pazar analizi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pazar analizi yapılırken hata oluştu: {str(e)}"
        )


@router.post("/analyze/{product_id}/customer")
async def analyze_customer_only(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Sadece hedef kitle analizi yap"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    try:
        print(f"🎯 Hedef kitle analizi başlatılıyor: {product.name}")
        customer_result = await strategy_builder.analyze_customer_only(product)
        print(f"✅ Hedef kitle analizi tamamlandı: {product.name}")
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "analysis_type": "customer",
            "result": customer_result,
            "message": "Hedef kitle analizi tamamlandı"
        }
        
    except Exception as e:
        print(f"❌ Hedef kitle analizi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hedef kitle analizi yapılırken hata oluştu: {str(e)}"
        )


@router.post("/analyze/{product_id}/pricing")
async def analyze_pricing_only(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Sadece fiyatlandırma analizi yap"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    try:
        print(f"💰 Fiyatlandırma analizi başlatılıyor: {product.name}")
        pricing_result = await strategy_builder.analyze_pricing_only(product)
        print(f"✅ Fiyatlandırma analizi tamamlandı: {product.name}")
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "analysis_type": "pricing",
            "result": pricing_result,
            "message": "Fiyatlandırma analizi tamamlandı"
        }
        
    except Exception as e:
        print(f"❌ Fiyatlandırma analizi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fiyatlandırma analizi yapılırken hata oluştu: {str(e)}"
        )


@router.post("/analyze/{product_id}/messaging")
async def analyze_messaging_only(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Sadece mesajlaşma stratejisi analizi yap"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    try:
        print(f"✍️ Mesajlaşma analizi başlatılıyor: {product.name}")
        messaging_result = await strategy_builder.analyze_messaging_only(product)
        print(f"✅ Mesajlaşma analizi tamamlandı: {product.name}")
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "analysis_type": "messaging",
            "result": messaging_result,
            "message": "Mesajlaşma analizi tamamlandı"
        }
        
    except Exception as e:
        print(f"❌ Mesajlaşma analizi hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mesajlaşma analizi yapılırken hata oluştu: {str(e)}"
        )


@router.post("/generate/{product_id}")
async def generate_strategy_only(
    product_id: int,
    request_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Analiz sonuçlarından nihai stratejiyi oluştur"""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı"
        )
    
    try:
        print(f"🚀 Nihai strateji oluşturuluyor: {product.name}")
        
        # Tüm analiz sonuçlarını birleştir
        combined_data = {
            "market_analysis": request_data.get("market_data", {}),
            "customer_analysis": request_data.get("customer_data", {}),
            "pricing_analysis": request_data.get("pricing_data", {}),
            "messaging_analysis": request_data.get("messaging_data", {})
        }
        
        strategy_result = await strategy_builder.generate_final_strategy(product, combined_data)
        print(f"✅ Nihai strateji oluşturuldu: {product.name}")
        
        return {
            "product_id": product_id,
            "product_name": product.name,
            "analysis_type": "final_strategy",
            "result": strategy_result,
            "message": "Nihai strateji oluşturuldu"
        }
        
    except Exception as e:
        print(f"❌ Strateji oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strateji oluşturulurken hata oluştu: {str(e)}"
        ) 