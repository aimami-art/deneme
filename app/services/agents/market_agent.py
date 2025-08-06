"""
Market Research Agent - Pazar araştırması agent'ı
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime
import logging

from app.services.a2a_network import A2AAgent, A2ATask, A2ATaskType
from app.services.ai_services import MarketAnalyzer
from app.services.serp_service import SerpApiService

logger = logging.getLogger(__name__)

class MarketResearchAgent(A2AAgent):
    """Market Research Agent - Pazar araştırması ve rakip analizi"""
    
    def __init__(self, agent_id: str = "market_research_agent_001"):
        capabilities = [
            "market_analysis",
            "competitor_research",
            "trend_analysis",
            "price_research"
        ]
        
        super().__init__(agent_id, "MarketResearchAgent", capabilities)
        
        # Servisler
        self.market_analyzer = MarketAnalyzer()
        self.serp_service = SerpApiService()
        
        self.max_concurrent_tasks = 3
    
    async def _execute_task(self, task: A2ATask):
        """Görevi çalıştır"""
        try:
            logger.info(f"🔍 Market Research Agent görevi başlıyor: {task.task_type.value}")
            
            if task.task_type == A2ATaskType.MARKET_ANALYSIS:
                result = await self._perform_market_analysis(task.input_data)
            elif task.task_type == A2ATaskType.COMPETITOR_RESEARCH:
                result = await self._research_competitors(task.input_data)
            else:
                result = await self._default_research_task(task.input_data)
            
            await self._complete_task(task.task_id, result)
            logger.info(f"✅ Market Research Agent görevi tamamlandı: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Market Research Agent görev hatası: {e}")
            await self._fail_task(task.task_id, str(e))
    
    async def _perform_market_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pazar analizi yap"""
        product_name = input_data.get("product_name", "")
        product_category = input_data.get("product_category", "")
        
        # AI ile pazar analizi
        market_analysis = await self.market_analyzer.analyze_market(product_name, product_category)
        
        return {
            "analysis_type": "comprehensive_market_analysis",
            "product_name": product_name,
            "product_category": product_category,
            "market_analysis": market_analysis,
            "analyzed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _research_competitors(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rakip araştırması yap"""
        product_name = input_data.get("product_name", "")
        
        # SerpAPI ile rakip araştırması
        competitor_data = await self.serp_service.search_competitors(product_name)
        
        return {
            "research_type": "competitor_analysis",
            "product_name": product_name,
            "competitor_data": competitor_data,
            "researched_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _default_research_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Varsayılan araştırma görevi"""
        return {
            "status": "completed",
            "message": "Market Research Agent tarafından işlendi",
            "input_data": input_data,
            "processed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        } 