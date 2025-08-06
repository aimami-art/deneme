"""
Performans Takibi API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.strategy import PerformanceData, Strategy
from app.models.product import Product
from app.schemas.strategy import PerformanceDataCreate, PerformanceDataResponse
from app.services.auth_service import AuthService
from app.models.user import User
from app.services.performance_analyzer import PerformanceAnalyzer

router = APIRouter()


@router.post("/", response_model=PerformanceDataResponse)
async def create_performance_data(
    performance_data: PerformanceDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Yeni performans verisi ekle"""
    print(f"📝 Performans verisi ekleniyor - Product ID: {performance_data.product_id}, User ID: {current_user.id}")
    
    # Ürün kontrolü
    product = db.query(Product).filter(
        Product.id == performance_data.product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        print(f"❌ Ürün bulunamadı - Product ID: {performance_data.product_id}, User ID: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı veya size ait değil"
        )
    
    print(f"✅ Ürün bulundu: {product.name}")
    
    # Strateji kontrolü (opsiyonel)
    if performance_data.strategy_id:
        strategy = db.query(Strategy).filter(
            Strategy.id == performance_data.strategy_id,
            Strategy.user_id == current_user.id
        ).first()
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strateji bulunamadı veya size ait değil"
            )
        print(f"✅ Strateji bulundu: {strategy.title}")
    else:
        print("ℹ️ Strateji seçilmedi")
    
    # Performans verisi oluştur
    db_performance = PerformanceData(
        sales_amount=performance_data.sales_amount,
        units_sold=performance_data.units_sold,
        conversion_rate=performance_data.conversion_rate,
        customer_acquisition_cost=performance_data.customer_acquisition_cost,
        roi=performance_data.roi,
        period_start=performance_data.period_start,
        period_end=performance_data.period_end,
        product_id=performance_data.product_id,
        strategy_id=performance_data.strategy_id
    )
    
    print(f"💾 Veritabanına kaydediliyor - Sales: {performance_data.sales_amount}, Units: {performance_data.units_sold}")
    
    db.add(db_performance)
    db.commit()
    db.refresh(db_performance)
    
    print(f"✅ Performans verisi oluşturuldu: ID {db_performance.id}, Product ID: {db_performance.product_id}")
    
    # Kontrol için toplam performans verisi sayısını göster
    total_count = db.query(PerformanceData).filter(
        PerformanceData.product_id == performance_data.product_id
    ).count()
    print(f"📊 Bu ürün için toplam performans verisi sayısı: {total_count}")
    
    return db_performance


@router.get("/product/{product_id}", response_model=List[PerformanceDataResponse])
async def get_product_performance(
    product_id: int,
    strategy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Ürün performans verilerini getir"""
    # Ürün kontrolü
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı veya size ait değil"
        )
    
    # Performans verilerini sorgula
    query = db.query(PerformanceData).filter(PerformanceData.product_id == product_id)
    
    if strategy_id:
        query = query.filter(PerformanceData.strategy_id == strategy_id)
    
    performance_data = query.order_by(PerformanceData.period_start.desc()).all()
    
    return performance_data


@router.get("/strategy/{strategy_id}", response_model=List[PerformanceDataResponse])
async def get_strategy_performance(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Strateji performans verilerini getir"""
    # Strateji kontrolü
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.user_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strateji bulunamadı veya size ait değil"
        )
    
    # Performans verilerini sorgula
    performance_data = db.query(PerformanceData).filter(
        PerformanceData.strategy_id == strategy_id
    ).order_by(PerformanceData.period_start.desc()).all()
    
    return performance_data


@router.get("/", response_model=List[PerformanceDataResponse])
async def get_all_performance_data(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Kullanıcının tüm performans verilerini getir"""
    # Kullanıcının ürünleri üzerinden performans verilerini getir
    performance_data = db.query(PerformanceData).join(Product).filter(
        Product.owner_id == current_user.id
    ).order_by(PerformanceData.period_start.desc()).offset(skip).limit(limit).all()
    
    return performance_data


@router.delete("/{performance_id}")
async def delete_performance_data(
    performance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Performans verisini sil"""
    # Performans verisi kontrolü
    performance = db.query(PerformanceData).join(Product).filter(
        PerformanceData.id == performance_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performans verisi bulunamadı veya size ait değil"
        )
    
    # Sil
    db.delete(performance)
    db.commit()
    
    print(f"✅ Performans verisi silindi: ID {performance_id}")
    return {"message": "Performans verisi başarıyla silindi"}


@router.post("/analyze/{product_id}")
async def analyze_performance_and_suggest_strategies(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Ürün performansını analiz et ve yeni stratejiler öner"""
    print(f"🔍 AI analizi başlatılıyor - Product ID: {product_id}, User ID: {current_user.id}")
    
    # Ürün kontrolü
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        print(f"❌ Ürün bulunamadı - Product ID: {product_id}, User ID: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı veya size ait değil"
        )
    
    print(f"✅ Ürün bulundu: {product.name}")
    
    # Performans verisi kontrolü - detaylı log
    performance_count = db.query(PerformanceData).filter(
        PerformanceData.product_id == product_id
    ).count()
    
    print(f"📊 Performans verisi sayısı: {performance_count} (Product ID: {product_id})")
    
    # Tüm performans verilerini listele (debug için)
    all_performance = db.query(PerformanceData).filter(
        PerformanceData.product_id == product_id
    ).all()
    
    for perf in all_performance:
        print(f"   - Performance ID: {perf.id}, Product ID: {perf.product_id}, Sales: {perf.sales_amount}")
    
    if performance_count == 0:
        print(f"❌ Performans verisi bulunamadı - Product ID: {product_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ürün için performans verisi bulunamadı. Önce performans verisi ekleyin."
        )
    
    print(f"✅ Performans verisi bulundu, AI analizi başlatılıyor...")
    
    # Performans analizi yap
    analyzer = PerformanceAnalyzer()
    analysis_result = await analyzer.analyze_performance_and_suggest_strategies(
        product_id, db, current_user.id
    )
    
    if not analysis_result.get("success", False):
        print(f"❌ AI analizi başarısız: {analysis_result.get('error', 'Bilinmeyen hata')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=analysis_result.get("error", "Performans analizi yapılamadı")
        )
    
    print(f"✅ AI analizi tamamlandı")
    return analysis_result


@router.post("/create-strategy/{product_id}")
async def create_strategy_from_performance_analysis(
    product_id: int,
    strategy_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Performans analizinden çıkan stratejiyi kaydet"""
    # Ürün kontrolü
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı veya size ait değil"
        )
    
    # Gerekli alanları kontrol et
    required_fields = ["title", "content"]
    for field in required_fields:
        if field not in strategy_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gerekli alan eksik: {field}"
            )
    
    try:
        # Performans analizi servisini kullan
        analyzer = PerformanceAnalyzer()
        new_strategy = await analyzer.create_strategy_from_performance(
            product_id, strategy_data, db, current_user.id
        )
        
        return {
            "message": "Strateji başarıyla oluşturuldu",
            "strategy_id": new_strategy.id,
            "strategy_title": new_strategy.title
        }
        
    except Exception as e:
        print(f"❌ Strateji oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Strateji oluşturulurken hata oluştu"
        )


@router.get("/insights/{product_id}")
async def get_performance_insights(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Ürün için performans içgörüleri getir"""
    # Ürün kontrolü
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.owner_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün bulunamadı veya size ait değil"
        )
    
    # Performans analizi yap (sadece analiz, strateji önerisi olmadan)
    analyzer = PerformanceAnalyzer()
    performance_data = await analyzer._get_performance_data(product_id, db)
    
    if not performance_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu ürün için performans verisi bulunamadı"
        )
    
    # Performans trendlerini analiz et
    performance_analysis = await analyzer._analyze_performance_trends(performance_data)
    
    # Strateji karşılaştırması yap
    performance_comparison = await analyzer._compare_strategy_performance(product_id, db)
    
    return {
        "product_name": product.name,
        "performance_analysis": performance_analysis,
        "strategy_comparison": performance_comparison,
        "analysis_timestamp": datetime.now().isoformat()
    } 