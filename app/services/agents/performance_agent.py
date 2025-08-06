"""
Performance Analysis Agent - Performans analizi agent'ı
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime
import logging

from app.services.a2a_network import A2AAgent, A2ATask, A2ATaskType
from app.services.performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class PerformanceAnalysisAgent(A2AAgent):
    """Performance Analysis Agent - Performans analizi ve optimizasyon"""
    
    def __init__(self, agent_id: str = "performance_analysis_agent_001"):
        capabilities = [
            "performance_analysis",
            "optimization_suggestions",
            "trend_analysis",
            "roi_calculation"
        ]
        
        super().__init__(agent_id, "PerformanceAnalysisAgent", capabilities)
        
        # Servisler
        self.performance_analyzer = PerformanceAnalyzer()
        
        self.max_concurrent_tasks = 2
    
    async def _execute_task(self, task: A2ATask):
        """Görevi çalıştır"""
        try:
            logger.info(f"📊 Performance Analysis Agent görevi başlıyor: {task.task_type.value}")
            
            if task.task_type == A2ATaskType.PERFORMANCE_ANALYSIS:
                result = await self._analyze_performance(task.input_data)
            else:
                result = await self._default_performance_task(task.input_data)
            
            await self._complete_task(task.task_id, result)
            logger.info(f"✅ Performance Analysis Agent görevi tamamlandı: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Performance Analysis Agent görev hatası: {e}")
            await self._fail_task(task.task_id, str(e))
    
    async def _analyze_performance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Performans analizi yap"""
        product_id = input_data.get("product_id")
        
        if not product_id:
            raise ValueError("Product ID gerekli")
        
        # Performans analizi
        analysis_result = await self.performance_analyzer.analyze_performance_and_suggest_strategies(product_id)
        
        return {
            "analysis_type": "comprehensive_performance_analysis",
            "product_id": product_id,
            "performance_analysis": analysis_result,
            "analyzed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _default_performance_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Varsayılan performans görevi"""
        return {
            "status": "completed",
            "message": "Performance Analysis Agent tarafından işlendi",
            "input_data": input_data,
            "processed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        } 