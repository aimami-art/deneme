"""
Agent Orchestrator Service
Tüm AI agent sistemini yöneten ana orkestratör servis
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from app.services.mcp_service import mcp_service
from app.services.a2a_network import a2a_network
from app.services.agents.strategy_agent import StrategyAgent
from app.services.agents.coordinator_agent import CoordinatorAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Agent Orchestrator - Tüm agent sistemini yöneten ana servis"""
    
    def __init__(self):
        self.is_running = False
        self.agents: Dict[str, Any] = {}
        self.system_stats = {
            "started_at": None,
            "total_tasks_processed": 0,
            "active_agents": 0,
            "system_health": "unknown"
        }
    
    async def start(self):
        """Agent sistemini başlat"""
        if self.is_running:
            logger.warning("⚠️ Agent Orchestrator zaten çalışıyor")
            return
        
        try:
            logger.info("🚀 Agent Orchestrator başlatılıyor...")
            
            # 1. MCP Service'i başlat
            await mcp_service.start()
            logger.info("✅ MCP Service başlatıldı")
            
            # 2. A2A Network'ü başlat
            await a2a_network.start()
            logger.info("✅ A2A Network başlatıldı")
            
            # 3. Agent'ları oluştur ve ağa ekle
            await self._initialize_agents()
            logger.info("✅ Agent'lar başlatıldı")
            
            # 4. Sistem durumunu güncelle
            self.is_running = True
            self.system_stats["started_at"] = datetime.now()
            self.system_stats["system_health"] = "healthy"
            
            logger.info("🎉 Agent Orchestrator başarıyla başlatıldı!")
            logger.info(f"📊 Aktif Agent Sayısı: {len(self.agents)}")
            
        except Exception as e:
            logger.error(f"❌ Agent Orchestrator başlatma hatası: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Agent sistemini durdur"""
        if not self.is_running:
            return
        
        logger.info("🛑 Agent Orchestrator durduruluyor...")
        
        try:
            # Agent'ları temizle
            self.agents.clear()
            
            # A2A Network'ü durdur
            await a2a_network.stop()
            logger.info("✅ A2A Network durduruldu")
            
            # MCP Service'i durdur
            await mcp_service.stop()
            logger.info("✅ MCP Service durduruldu")
            
            # Sistem durumunu güncelle
            self.is_running = False
            self.system_stats["system_health"] = "stopped"
            
            logger.info("🏁 Agent Orchestrator başarıyla durduruldu")
            
        except Exception as e:
            logger.error(f"❌ Agent Orchestrator durdurma hatası: {e}")
    
    async def _initialize_agents(self):
        """Agent'ları başlat"""
        try:
            # 1. Strategy Agent
            strategy_agent = StrategyAgent("strategy_agent_001")
            await strategy_agent.join_network(a2a_network)
            self.agents["strategy_agent_001"] = strategy_agent
            logger.info("🎯 Strategy Agent başlatıldı")
            
            # 2. Coordinator Agent
            coordinator_agent = CoordinatorAgent("coordinator_agent_001")
            await coordinator_agent.join_network(a2a_network)
            self.agents["coordinator_agent_001"] = coordinator_agent
            logger.info("🎼 Coordinator Agent başlatıldı")
            
            # Gelecekte daha fazla agent eklenebilir:
            # - MarketResearchAgent
            # - PerformanceAnalysisAgent
            # - CustomerServiceAgent
            # - PricingOptimizationAgent
            
            self.system_stats["active_agents"] = len(self.agents)
            
        except Exception as e:
            logger.error(f"❌ Agent başlatma hatası: {e}")
            raise
    
    async def orchestrate_comprehensive_strategy(self, product_id: int, user_id: int) -> Dict[str, Any]:
        """Kapsamlı strateji orkestrasyon"""
        if not self.is_running:
            raise RuntimeError("Agent Orchestrator çalışmıyor")
        
        coordinator = self.agents.get("coordinator_agent_001")
        if not coordinator:
            raise RuntimeError("Coordinator Agent bulunamadı")
        
        logger.info(f"🎼 Kapsamlı strateji orkestrasyon başlıyor: Product {product_id}")
        
        # Coordinator Agent'a orkestrasyon görevi ver
        result = await coordinator.orchestrate_comprehensive_strategy(product_id, user_id)
        
        # İstatistikleri güncelle
        self.system_stats["total_tasks_processed"] += 1
        
        return result
    
    async def create_strategy_with_agent(self, product_id: int, user_id: int, 
                                       analysis_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Agent ile strateji oluştur"""
        if not self.is_running:
            raise RuntimeError("Agent Orchestrator çalışmıyor")
        
        strategy_agent = self.agents.get("strategy_agent_001")
        if not strategy_agent:
            raise RuntimeError("Strategy Agent bulunamadı")
        
        logger.info(f"🎯 Strategy Agent ile strateji oluşturuluyor: Product {product_id}")
        
        if analysis_data:
            # Mevcut analiz verilerini kullan
            result = await strategy_agent.create_strategy_from_analysis(product_id, user_id, analysis_data)
        else:
            # Yeni analiz yap
            from app.services.a2a_network import A2ATaskType
            task_id = await strategy_agent.request_task(
                task_type=A2ATaskType.STRATEGY_GENERATION,
                input_data={
                    "product_id": product_id,
                    "user_id": user_id
                },
                priority=2
            )
            result = {"task_id": task_id, "status": "assigned"}
        
        # İstatistikleri güncelle
        self.system_stats["total_tasks_processed"] += 1
        
        return result
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Sistem durumu"""
        if not self.is_running:
            return {
                "status": "stopped",
                "message": "Agent Orchestrator çalışmıyor"
            }
        
        # MCP istatistikleri
        mcp_stats = await mcp_service.get_service_stats()
        
        # A2A network istatistikleri
        a2a_stats = await a2a_network.get_network_stats()
        
        # Agent istatistikleri
        agent_stats = {}
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'get_agent_stats'):
                agent_stats[agent_id] = agent.get_agent_stats()
            elif hasattr(agent, 'get_coordinator_stats'):
                agent_stats[agent_id] = agent.get_coordinator_stats()
        
        # Sistem sağlık durumu
        system_health = "healthy"
        if (mcp_stats["service_uptime"] != "running" or 
            a2a_stats["network_status"] != "running"):
            system_health = "unhealthy"
        
        return {
            "status": "running",
            "system_health": system_health,
            "orchestrator_stats": self.system_stats,
            "mcp_stats": mcp_stats,
            "a2a_stats": a2a_stats,
            "agent_stats": agent_stats,
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if getattr(a, 'status', 'unknown') != 'offline']),
            "uptime": str(datetime.now() - self.system_stats["started_at"]) if self.system_stats["started_at"] else "0",
            "checked_at": datetime.now().isoformat()
        }
    
    async def get_agent_performance(self) -> Dict[str, Any]:
        """Agent performans raporu"""
        if not self.is_running:
            return {"error": "Agent Orchestrator çalışmıyor"}
        
        coordinator = self.agents.get("coordinator_agent_001")
        if not coordinator:
            return {"error": "Coordinator Agent bulunamadı"}
        
        # Coordinator Agent'tan performans analizi iste
        from app.services.a2a_network import A2ATaskType
        task_id = await coordinator.request_task(
            task_type=A2ATaskType.COORDINATION,
            input_data={
                "type": "agent_performance_analysis",
                "period": "last_hour"
            },
            priority=1
        )
        
        return {
            "performance_analysis_task": task_id,
            "status": "analysis_requested",
            "message": "Performans analizi başlatıldı"
        }
    
    async def monitor_system_health(self) -> Dict[str, Any]:
        """Sistem sağlık izleme"""
        if not self.is_running:
            return {"error": "Agent Orchestrator çalışmıyor"}
        
        coordinator = self.agents.get("coordinator_agent_001")
        if not coordinator:
            return {"error": "Coordinator Agent bulunamadı"}
        
        # Coordinator Agent'tan sistem izleme iste
        from app.services.a2a_network import A2ATaskType
        task_id = await coordinator.request_task(
            task_type=A2ATaskType.COORDINATION,
            input_data={
                "type": "system_monitoring",
                "scope": "all"
            },
            priority=2
        )
        
        return {
            "monitoring_task": task_id,
            "status": "monitoring_started",
            "message": "Sistem izleme başlatıldı"
        }
    
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """Orchestrator bilgileri"""
        return {
            "name": "Agent Orchestrator",
            "version": "1.0.0",
            "description": "AI Agent sistemini yöneten ana orkestratör servis",
            "is_running": self.is_running,
            "capabilities": [
                "Agent Lifecycle Management",
                "MCP Communication",
                "A2A Network Coordination",
                "Workflow Orchestration",
                "System Monitoring",
                "Performance Analysis"
            ],
            "supported_agents": [
                "StrategyAgent",
                "CoordinatorAgent",
                "MarketResearchAgent (planned)",
                "PerformanceAnalysisAgent (planned)"
            ],
            "stats": self.system_stats
        }

# Global Agent Orchestrator instance
agent_orchestrator = AgentOrchestrator()

# Lifespan context manager for FastAPI
@asynccontextmanager
async def agent_lifespan(app):
    """FastAPI lifespan context manager"""
    # Startup
    try:
        await agent_orchestrator.start()
        logger.info("🎉 Agent sistem FastAPI ile başlatıldı")
        yield
    finally:
        # Shutdown
        await agent_orchestrator.stop()
        logger.info("🏁 Agent sistem FastAPI ile durduruldu") 