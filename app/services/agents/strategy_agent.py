"""
Strategy Agent - Strateji oluşturma ve analiz agent'ı
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.services.a2a_network import A2AAgent, A2ATask, A2ATaskType
from app.services.ai_services import StrategyBuilder, MarketAnalyzer, CustomerSegmenter, PricingAdvisor, MessagingGenerator
from app.services.rag_engine import RAGEmbeddingEngine
from app.models.product import Product
from app.models.strategy import Strategy
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class StrategyAgent(A2AAgent):
    """AI Strategy Agent - Gelişmiş strateji oluşturma agent'ı"""
    
    def __init__(self, agent_id: str = "strategy_agent_001"):
        capabilities = [
            "strategy_generation",
            "market_analysis", 
            "customer_segmentation",
            "price_optimization",
            "messaging_strategy"
        ]
        
        super().__init__(agent_id, "StrategyAgent", capabilities)
        
        # AI Servisleri
        self.strategy_builder = StrategyBuilder()
        self.market_analyzer = MarketAnalyzer()
        self.customer_segmenter = CustomerSegmenter()
        self.pricing_advisor = PricingAdvisor()
        self.messaging_generator = MessagingGenerator()
        
        # RAG Engine
        self.rag_engine = RAGEmbeddingEngine()
        
        self.max_concurrent_tasks = 2  # Strateji oluşturma resource-intensive
    
    async def _execute_task(self, task: A2ATask):
        """Görevi çalıştır"""
        try:
            logger.info(f"🎯 Strategy Agent görevi başlıyor: {task.task_type.value}")
            
            if task.task_type == A2ATaskType.STRATEGY_GENERATION:
                result = await self._generate_comprehensive_strategy(task.input_data)
            elif task.task_type == A2ATaskType.MARKET_ANALYSIS:
                result = await self._perform_market_analysis(task.input_data)
            elif task.task_type == A2ATaskType.CUSTOMER_SEGMENTATION:
                result = await self._segment_customers(task.input_data)
            elif task.task_type == A2ATaskType.PRICE_OPTIMIZATION:
                result = await self._optimize_pricing(task.input_data)
            else:
                result = await self._default_strategy_task(task.input_data)
            
            await self._complete_task(task.task_id, result)
            logger.info(f"✅ Strategy Agent görevi tamamlandı: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Strategy Agent görev hatası: {e}")
            await self._fail_task(task.task_id, str(e))
    
    async def _generate_comprehensive_strategy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kapsamlı strateji oluştur"""
        product_id = input_data.get("product_id")
        user_id = input_data.get("user_id")
        strategy_requirements = input_data.get("requirements", {})
        
        if not product_id:
            raise ValueError("Product ID gerekli")
        
        # Database session
        db: Session = next(get_db())
        
        try:
            # Ürün bilgilerini al
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Ürün bulunamadı: {product_id}")
            
            # RAG ile benzer stratejileri ara
            similar_strategies = await self.rag_engine.search_similar_strategies(
                query=f"{product.name} {product.category} satış stratejisi",
                user_id=user_id,
                top_k=3,
                min_score=0.6
            )
            
            # Context bilgilerini topla
            context_data = {
                "product": {
                    "name": product.name,
                    "description": product.description,
                    "category": product.category,
                    "cost_price": float(product.cost_price),
                    "target_profit_margin": float(product.target_profit_margin or 0.2)
                },
                "similar_strategies": similar_strategies,
                "requirements": strategy_requirements
            }
            
            # MCP ile context paylaş
            await self.network.network.context_store.share_context(
                sender_id=self.agent_id,
                context_key=f"strategy_context_{product_id}",
                context_data=context_data,
                ttl_minutes=60
            )
            
            # Paralel AI analizi başlat
            market_task = asyncio.create_task(
                self.market_analyzer.analyze_market(product.name, product.category)
            )
            
            customer_task = asyncio.create_task(
                self.customer_segmenter.segment_customers(product.name, product.category)
            )
            
            pricing_task = asyncio.create_task(
                self.pricing_advisor.suggest_pricing(
                    product.name, 
                    product.category, 
                    float(product.cost_price),
                    float(product.target_profit_margin or 0.2)
                )
            )
            
            messaging_task = asyncio.create_task(
                self.messaging_generator.generate_messaging(product.name, product.category)
            )
            
            # Tüm analizleri bekle
            market_analysis, customer_segments, pricing_recommendations, messaging_content = await asyncio.gather(
                market_task, customer_task, pricing_task, messaging_task
            )
            
            # Ana strateji oluştur
            strategy_data = {
                "market_analysis": market_analysis,
                "customer_segments": customer_segments,
                "pricing_recommendations": pricing_recommendations,
                "messaging_content": messaging_content,
                "similar_strategies_count": len(similar_strategies)
            }
            
            comprehensive_strategy = await self.strategy_builder.build_strategy(
                product_name=product.name,
                product_category=product.category,
                analysis_data=strategy_data
            )
            
            # Sonucu hazırla
            result = {
                "strategy_id": f"strategy_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "product_id": product_id,
                "comprehensive_strategy": comprehensive_strategy,
                "analysis_components": {
                    "market_analysis": market_analysis,
                    "customer_segments": customer_segments,
                    "pricing_recommendations": pricing_recommendations,
                    "messaging_content": messaging_content
                },
                "similar_strategies_used": len(similar_strategies),
                "confidence_score": comprehensive_strategy.get("confidence_score", 0.8),
                "expected_roi": comprehensive_strategy.get("expected_roi", 0.15),
                "implementation_difficulty": comprehensive_strategy.get("implementation_difficulty", "medium"),
                "generated_at": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            return result
            
        finally:
            db.close()
    
    async def _perform_market_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pazar analizi yap"""
        product_name = input_data.get("product_name")
        product_category = input_data.get("product_category")
        
        if not product_name or not product_category:
            raise ValueError("Product name ve category gerekli")
        
        # Detaylı pazar analizi
        market_analysis = await self.market_analyzer.analyze_market(product_name, product_category)
        
        return {
            "analysis_type": "market_analysis",
            "product_name": product_name,
            "product_category": product_category,
            "market_analysis": market_analysis,
            "analyzed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _segment_customers(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Müşteri segmentasyonu yap"""
        product_name = input_data.get("product_name")
        product_category = input_data.get("product_category")
        
        if not product_name or not product_category:
            raise ValueError("Product name ve category gerekli")
        
        # Müşteri segmentasyonu
        customer_segments = await self.customer_segmenter.segment_customers(product_name, product_category)
        
        return {
            "analysis_type": "customer_segmentation",
            "product_name": product_name,
            "product_category": product_category,
            "customer_segments": customer_segments,
            "analyzed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _optimize_pricing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fiyat optimizasyonu yap"""
        product_name = input_data.get("product_name")
        product_category = input_data.get("product_category")
        cost_price = input_data.get("cost_price")
        target_margin = input_data.get("target_margin", 0.2)
        
        if not all([product_name, product_category, cost_price]):
            raise ValueError("Product name, category ve cost_price gerekli")
        
        # Fiyat optimizasyonu
        pricing_recommendations = await self.pricing_advisor.suggest_pricing(
            product_name, product_category, cost_price, target_margin
        )
        
        return {
            "analysis_type": "price_optimization",
            "product_name": product_name,
            "product_category": product_category,
            "cost_price": cost_price,
            "target_margin": target_margin,
            "pricing_recommendations": pricing_recommendations,
            "analyzed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _default_strategy_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Varsayılan strateji görevi"""
        return {
            "status": "completed",
            "message": "Strategy Agent tarafından işlendi",
            "input_data": input_data,
            "processed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def create_strategy_from_analysis(self, product_id: int, user_id: int, 
                                          analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiz verilerinden strateji oluştur"""
        task_input = {
            "product_id": product_id,
            "user_id": user_id,
            "requirements": {
                "use_existing_analysis": True,
                "analysis_data": analysis_data
            }
        }
        
        # Görev olarak ata
        task_id = await self.request_task(
            task_type=A2ATaskType.STRATEGY_GENERATION,
            input_data=task_input,
            priority=2
        )
        
        return {"task_id": task_id, "status": "assigned"}
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Agent istatistikleri"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "capabilities": self.capabilities,
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": list(self.current_tasks)
        } 