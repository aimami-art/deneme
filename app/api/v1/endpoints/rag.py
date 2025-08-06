"""
RAG & Vector Search API Endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.strategy import Strategy
from app.models.product import Product
from app.services.auth_service import AuthService
from app.models.user import User
from app.services.rag_engine import RAGEmbeddingEngine

router = APIRouter()

# RAG Engine instance
rag_engine = RAGEmbeddingEngine()


class VectorSearchRequest(BaseModel):
    """Vector arama isteği"""
    query: str
    product_category: Optional[str] = None
    top_k: int = 5
    min_score: float = 0.7


class RAGQueryRequest(BaseModel):
    """RAG soru-cevap isteği"""
    question: str
    product_context: Optional[Dict[str, Any]] = None
    max_context_length: int = 3000


class StrategyEmbeddingRequest(BaseModel):
    """Strateji embedding isteği"""
    strategy_id: int


@router.post("/search")
async def search_similar_strategies(
    request: VectorSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Vector tabanlı strateji arama"""
    try:
        similar_strategies = await rag_engine.search_similar_strategies(
            query=request.query,
            user_id=current_user.id,
            product_category=request.product_category,
            top_k=request.top_k,
            min_score=request.min_score
        )
        
        return {
            "success": True,
            "query": request.query,
            "results_count": len(similar_strategies),
            "similar_strategies": similar_strategies,
            "search_params": {
                "product_category": request.product_category,
                "top_k": request.top_k,
                "min_score": request.min_score
            }
        }
        
    except Exception as e:
        print(f"❌ Vector arama hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector arama yapılırken hata oluştu: {str(e)}"
        )


@router.post("/ask")
async def rag_question_answer(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """RAG tabanlı soru-cevap sistemi"""
    try:
        rag_response = await rag_engine.generate_rag_response(
            question=request.question,
            user_id=current_user.id,
            product_context=request.product_context,
            max_context_length=request.max_context_length
        )
        
        return {
            "success": True,
            "question": request.question,
            "answer": rag_response["answer"],
            "sources": rag_response["sources"],
            "confidence": rag_response["confidence"],
            "context_used": rag_response.get("context_used", 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ RAG soru-cevap hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG soru-cevap işlemi sırasında hata oluştu: {str(e)}"
        )


@router.post("/embed-strategy")
async def embed_strategy_to_vector_db(
    request: StrategyEmbeddingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Stratejiyi vector veritabanına ekle"""
    try:
        # Stratejiyi kontrol et
        strategy = db.query(Strategy).filter(
            Strategy.id == request.strategy_id,
            Strategy.user_id == current_user.id
        ).first()
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strateji bulunamadı veya size ait değil"
            )
        
        # Ürün bilgisini al
        product = db.query(Product).filter(
            Product.id == strategy.product_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strateji ile ilişkili ürün bulunamadı"
            )
        
        # Vector DB'ye ekle
        success = await rag_engine.add_strategy_to_vector_db(strategy, product, db)
        
        if success:
            return {
                "success": True,
                "message": f"Strateji başarıyla vector veritabanına eklendi: {strategy.title}",
                "strategy_id": strategy.id,
                "strategy_title": strategy.title,
                "product_name": product.name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Strateji vector veritabanına eklenemedi"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Strateji embedding hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strateji embedding işlemi sırasında hata oluştu: {str(e)}"
        )


@router.delete("/strategy/{strategy_id}")
async def remove_strategy_from_vector_db(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Stratejiyi vector veritabanından sil"""
    try:
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
        
        # Vector DB'den sil
        success = await rag_engine.delete_strategy_from_vector_db(strategy_id)
        
        if success:
            return {
                "success": True,
                "message": f"Strateji vector veritabanından silindi: {strategy.title}",
                "strategy_id": strategy_id
            }
        else:
            return {
                "success": False,
                "message": "Strateji vector veritabanından silinemedi",
                "strategy_id": strategy_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Vector DB silme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector veritabanından silme işlemi sırasında hata oluştu: {str(e)}"
        )


@router.get("/stats")
async def get_vector_db_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Vector veritabanı istatistikleri"""
    try:
        stats = await rag_engine.get_vector_db_stats(user_id=current_user.id)
        
        return {
            "success": True,
            "user_id": current_user.id,
            "vector_db_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Vector DB stats hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector veritabanı istatistikleri alınırken hata oluştu: {str(e)}"
        )


@router.post("/batch-embed")
async def batch_embed_user_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Kullanıcının tüm stratejilerini toplu olarak vector DB'ye ekle"""
    try:
        # Kullanıcının tüm stratejilerini al
        strategies = db.query(Strategy).filter(
            Strategy.user_id == current_user.id
        ).all()
        
        if not strategies:
            return {
                "success": True,
                "message": "Eklenecek strateji bulunamadı",
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0
            }
        
        success_count = 0
        failed_count = 0
        failed_strategies = []
        
        for strategy in strategies:
            try:
                # Ürün bilgisini al
                product = db.query(Product).filter(
                    Product.id == strategy.product_id
                ).first()
                
                if product:
                    success = await rag_engine.add_strategy_to_vector_db(strategy, product, db)
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_strategies.append({
                            "strategy_id": strategy.id,
                            "title": strategy.title,
                            "error": "Vector DB'ye ekleme başarısız"
                        })
                else:
                    failed_count += 1
                    failed_strategies.append({
                        "strategy_id": strategy.id,
                        "title": strategy.title,
                        "error": "İlişkili ürün bulunamadı"
                    })
                    
            except Exception as e:
                failed_count += 1
                failed_strategies.append({
                    "strategy_id": strategy.id,
                    "title": strategy.title,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"Toplu embedding tamamlandı",
            "processed_count": len(strategies),
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_strategies": failed_strategies[:5],  # İlk 5 hatayı göster
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Toplu embedding hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Toplu embedding işlemi sırasında hata oluştu: {str(e)}"
        )


# Import datetime for timestamp
from datetime import datetime 