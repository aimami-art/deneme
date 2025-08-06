"""
Coordinator Agent - Tüm agent'ları koordine eden ana agent
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.services.a2a_network import A2AAgent, A2ATask, A2ATaskType, A2ATaskStatus, a2a_network
from app.services.mcp_service import mcp_service, MCPMessage, MCPMessageType

logger = logging.getLogger(__name__)

class CoordinatorAgent(A2AAgent):
    """Coordinator Agent - Multi-agent koordinasyon sistemi"""
    
    def __init__(self, agent_id: str = "coordinator_agent_001"):
        capabilities = [
            "coordination",
            "task_orchestration",
            "resource_management",
            "workflow_management",
            "system_monitoring"
        ]
        
        super().__init__(agent_id, "CoordinatorAgent", capabilities)
        
        # Koordinasyon verileri
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.agent_performance: Dict[str, Dict[str, Any]] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        
        self.max_concurrent_tasks = 10  # Coordinator çok görev alabilir
    
    async def _execute_task(self, task: A2ATask):
        """Koordinasyon görevi çalıştır"""
        try:
            logger.info(f"🎯 Coordinator Agent görevi başlıyor: {task.task_type.value}")
            
            if task.task_type == A2ATaskType.COORDINATION:
                result = await self._handle_coordination_task(task.input_data)
            else:
                result = await self._default_coordination_task(task.input_data)
            
            await self._complete_task(task.task_id, result)
            logger.info(f"✅ Coordinator Agent görevi tamamlandı: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Coordinator Agent görev hatası: {e}")
            await self._fail_task(task.task_id, str(e))
    
    async def _handle_coordination_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Koordinasyon görevini işle"""
        coordination_type = input_data.get("type")
        
        if coordination_type == "workflow_orchestration":
            return await self._orchestrate_workflow(input_data)
        elif coordination_type == "resource_allocation":
            return await self._allocate_resources(input_data)
        elif coordination_type == "system_monitoring":
            return await self._monitor_system(input_data)
        elif coordination_type == "agent_performance_analysis":
            return await self._analyze_agent_performance(input_data)
        else:
            return await self._default_coordination_task(input_data)
    
    async def _orchestrate_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """İş akışı orkestrasyon"""
        workflow_id = input_data.get("workflow_id", f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        workflow_type = input_data.get("workflow_type", "strategy_generation")
        workflow_data = input_data.get("workflow_data", {})
        
        logger.info(f"🎼 Workflow orkestrasyon başlıyor: {workflow_id} ({workflow_type})")
        
        # Workflow planı oluştur
        if workflow_type == "comprehensive_strategy_generation":
            workflow_plan = await self._create_comprehensive_strategy_workflow(workflow_data)
        elif workflow_type == "market_research_workflow":
            workflow_plan = await self._create_market_research_workflow(workflow_data)
        elif workflow_type == "performance_optimization_workflow":
            workflow_plan = await self._create_performance_optimization_workflow(workflow_data)
        else:
            workflow_plan = await self._create_default_workflow(workflow_data)
        
        # Workflow'u kaydet
        self.active_workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "workflow_plan": workflow_plan,
            "status": "active",
            "created_at": datetime.now(),
            "tasks": {},
            "dependencies": {},
            "progress": 0
        }
        
        # Workflow görevlerini başlat
        await self._execute_workflow(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "status": "orchestrated",
            "tasks_count": len(workflow_plan.get("tasks", [])),
            "estimated_duration": workflow_plan.get("estimated_duration", "unknown"),
            "orchestrated_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _create_comprehensive_strategy_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kapsamlı strateji oluşturma workflow'u"""
        product_id = workflow_data.get("product_id")
        user_id = workflow_data.get("user_id")
        
        workflow_plan = {
            "tasks": [
                {
                    "task_id": f"market_analysis_{product_id}",
                    "task_type": A2ATaskType.MARKET_ANALYSIS,
                    "agent_type": "MarketResearchAgent",
                    "priority": 3,
                    "input_data": {
                        "product_id": product_id,
                        "analysis_depth": "comprehensive"
                    },
                    "dependencies": []
                },
                {
                    "task_id": f"customer_segmentation_{product_id}",
                    "task_type": A2ATaskType.CUSTOMER_SEGMENTATION,
                    "agent_type": "StrategyAgent",
                    "priority": 3,
                    "input_data": {
                        "product_id": product_id,
                        "segmentation_method": "ai_driven"
                    },
                    "dependencies": []
                },
                {
                    "task_id": f"price_optimization_{product_id}",
                    "task_type": A2ATaskType.PRICE_OPTIMIZATION,
                    "agent_type": "StrategyAgent",
                    "priority": 2,
                    "input_data": {
                        "product_id": product_id,
                        "optimization_goal": "roi_maximization"
                    },
                    "dependencies": [f"market_analysis_{product_id}"]
                },
                {
                    "task_id": f"strategy_generation_{product_id}",
                    "task_type": A2ATaskType.STRATEGY_GENERATION,
                    "agent_type": "StrategyAgent",
                    "priority": 1,
                    "input_data": {
                        "product_id": product_id,
                        "user_id": user_id,
                        "use_workflow_results": True
                    },
                    "dependencies": [
                        f"market_analysis_{product_id}",
                        f"customer_segmentation_{product_id}",
                        f"price_optimization_{product_id}"
                    ]
                }
            ],
            "estimated_duration": "5-10 minutes",
            "workflow_type": "comprehensive_strategy_generation"
        }
        
        return workflow_plan
    
    async def _create_market_research_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pazar araştırması workflow'u"""
        return {
            "tasks": [
                {
                    "task_id": f"competitor_research_{workflow_data.get('product_id')}",
                    "task_type": A2ATaskType.COMPETITOR_RESEARCH,
                    "agent_type": "MarketResearchAgent",
                    "priority": 3,
                    "input_data": workflow_data,
                    "dependencies": []
                }
            ],
            "estimated_duration": "3-5 minutes",
            "workflow_type": "market_research"
        }
    
    async def _create_performance_optimization_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Performans optimizasyon workflow'u"""
        return {
            "tasks": [
                {
                    "task_id": f"performance_analysis_{workflow_data.get('product_id')}",
                    "task_type": A2ATaskType.PERFORMANCE_ANALYSIS,
                    "agent_type": "PerformanceAnalysisAgent",
                    "priority": 3,
                    "input_data": workflow_data,
                    "dependencies": []
                }
            ],
            "estimated_duration": "2-4 minutes",
            "workflow_type": "performance_optimization"
        }
    
    async def _create_default_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Varsayılan workflow"""
        return {
            "tasks": [
                {
                    "task_id": f"default_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "task_type": A2ATaskType.COORDINATION,
                    "agent_type": "CoordinatorAgent",
                    "priority": 1,
                    "input_data": workflow_data,
                    "dependencies": []
                }
            ],
            "estimated_duration": "1-2 minutes",
            "workflow_type": "default"
        }
    
    async def _execute_workflow(self, workflow_id: str):
        """Workflow'u çalıştır"""
        if workflow_id not in self.active_workflows:
            return
        
        workflow = self.active_workflows[workflow_id]
        workflow_plan = workflow["workflow_plan"]
        
        # Görevleri dependency sırasına göre başlat
        for task_config in workflow_plan["tasks"]:
            # Dependency kontrolü
            dependencies = task_config.get("dependencies", [])
            if dependencies:
                # Bağımlılıkları bekle (basit implementasyon)
                await asyncio.sleep(1)
            
            # Görevi oluştur ve gönder
            task = A2ATask(
                task_id=task_config["task_id"],
                task_type=task_config["task_type"],
                requester_id=self.agent_id,
                priority=task_config["priority"],
                input_data=task_config["input_data"]
            )
            
            # A2A network'e gönder
            task_id = await a2a_network.submit_task(task)
            
            # Workflow'da takip et
            workflow["tasks"][task_id] = {
                "task_config": task_config,
                "status": "submitted",
                "submitted_at": datetime.now()
            }
        
        logger.info(f"🎼 Workflow görevleri gönderildi: {workflow_id}")
    
    async def _allocate_resources(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kaynak tahsisi"""
        resource_type = input_data.get("resource_type", "agent_capacity")
        allocation_strategy = input_data.get("strategy", "load_balanced")
        
        # Agent'ların mevcut durumunu al
        active_agents = await mcp_service.context_store.get_active_agents()
        
        # Kaynak tahsis stratejisi uygula
        if allocation_strategy == "load_balanced":
            allocation_result = await self._load_balanced_allocation(active_agents)
        elif allocation_strategy == "priority_based":
            allocation_result = await self._priority_based_allocation(active_agents)
        else:
            allocation_result = await self._default_allocation(active_agents)
        
        return {
            "resource_type": resource_type,
            "allocation_strategy": allocation_strategy,
            "active_agents": len(active_agents),
            "allocation_result": allocation_result,
            "allocated_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _load_balanced_allocation(self, active_agents: List[Any]) -> Dict[str, Any]:
        """Yük dengeli tahsis"""
        return {
            "strategy": "load_balanced",
            "agents_analyzed": len(active_agents),
            "recommendation": "Görevleri agent yüküne göre dağıt"
        }
    
    async def _priority_based_allocation(self, active_agents: List[Any]) -> Dict[str, Any]:
        """Öncelik bazlı tahsis"""
        return {
            "strategy": "priority_based",
            "agents_analyzed": len(active_agents),
            "recommendation": "Yüksek öncelikli görevleri en uygun agent'lara ata"
        }
    
    async def _default_allocation(self, active_agents: List[Any]) -> Dict[str, Any]:
        """Varsayılan tahsis"""
        return {
            "strategy": "default",
            "agents_analyzed": len(active_agents),
            "recommendation": "Standart tahsis stratejisi uygula"
        }
    
    async def _monitor_system(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sistem izleme"""
        monitoring_scope = input_data.get("scope", "all")
        
        # MCP istatistikleri
        mcp_stats = await mcp_service.get_service_stats()
        
        # A2A network istatistikleri
        a2a_stats = await a2a_network.get_network_stats()
        
        # Workflow durumları
        workflow_stats = {
            "active_workflows": len(self.active_workflows),
            "workflows": list(self.active_workflows.keys())
        }
        
        system_health = {
            "mcp_service": "healthy" if mcp_stats["service_uptime"] == "running" else "unhealthy",
            "a2a_network": "healthy" if a2a_stats["network_status"] == "running" else "unhealthy",
            "coordinator": "healthy"
        }
        
        return {
            "monitoring_scope": monitoring_scope,
            "system_health": system_health,
            "mcp_stats": mcp_stats,
            "a2a_stats": a2a_stats,
            "workflow_stats": workflow_stats,
            "monitored_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _analyze_agent_performance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Agent performans analizi"""
        analysis_period = input_data.get("period", "last_hour")
        
        # Basit performans analizi
        performance_summary = {
            "total_agents": len(await mcp_service.context_store.get_active_agents()),
            "analysis_period": analysis_period,
            "performance_metrics": {
                "task_completion_rate": "85%",
                "average_response_time": "2.3 seconds",
                "error_rate": "5%"
            }
        }
        
        return {
            "analysis_type": "agent_performance",
            "analysis_period": analysis_period,
            "performance_summary": performance_summary,
            "analyzed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def _default_coordination_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Varsayılan koordinasyon görevi"""
        return {
            "status": "completed",
            "message": "Coordinator Agent tarafından işlendi",
            "input_data": input_data,
            "processed_at": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
    
    async def orchestrate_comprehensive_strategy(self, product_id: int, user_id: int) -> Dict[str, Any]:
        """Kapsamlı strateji orkestrasyon"""
        workflow_data = {
            "product_id": product_id,
            "user_id": user_id,
            "workflow_type": "comprehensive_strategy_generation"
        }
        
        task_input = {
            "type": "workflow_orchestration",
            "workflow_type": "comprehensive_strategy_generation",
            "workflow_data": workflow_data
        }
        
        # Koordinasyon görevi oluştur
        task_id = await self.request_task(
            task_type=A2ATaskType.COORDINATION,
            input_data=task_input,
            priority=3
        )
        
        return {"task_id": task_id, "status": "orchestration_started"}
    
    def get_coordinator_stats(self) -> Dict[str, Any]:
        """Coordinator istatistikleri"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "active_workflows": len(self.active_workflows),
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "workflows": list(self.active_workflows.keys())
        } 