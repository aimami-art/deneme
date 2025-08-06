"""
Agent System API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging

from app.services.agent_orchestrator import agent_orchestrator
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/system/status")
async def get_agent_system_status():
    """Agent sistem durumunu al"""
    try:
        status = await agent_orchestrator.get_system_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Agent sistem durumu alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/info")
async def get_orchestrator_info():
    """Agent Orchestrator bilgilerini al"""
    try:
        info = agent_orchestrator.get_orchestrator_info()
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        logger.error(f"Orchestrator bilgisi alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy/orchestrate")
async def orchestrate_comprehensive_strategy(
    product_id: int,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Kapsamlı strateji orkestrasyon başlat"""
    try:
        if not agent_orchestrator.is_running:
            raise HTTPException(
                status_code=503, 
                detail="Agent sistemi çalışmıyor"
            )
        
        result = await agent_orchestrator.orchestrate_comprehensive_strategy(
            product_id=product_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Kapsamlı strateji orkestrasyon başlatıldı",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Strateji orkestrasyon hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy/create")
async def create_strategy_with_agent(
    product_id: int,
    analysis_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Agent ile strateji oluştur"""
    try:
        if not agent_orchestrator.is_running:
            raise HTTPException(
                status_code=503, 
                detail="Agent sistemi çalışmıyor"
            )
        
        result = await agent_orchestrator.create_strategy_with_agent(
            product_id=product_id,
            user_id=current_user.id,
            analysis_data=analysis_data
        )
        
        return {
            "success": True,
            "message": "Agent ile strateji oluşturma başlatıldı",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Agent strateji oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/analyze")
async def get_agent_performance():
    """Agent performans analizi al"""
    try:
        result = await agent_orchestrator.get_agent_performance()
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        return {
            "success": True,
            "message": "Agent performans analizi başlatıldı",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent performans analizi hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/monitor")
async def monitor_system_health():
    """Sistem sağlık izleme"""
    try:
        result = await agent_orchestrator.monitor_system_health()
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        
        return {
            "success": True,
            "message": "Sistem izleme başlatıldı",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sistem izleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/start")
async def start_agent_system():
    """Agent sistemini başlat (admin only)"""
    try:
        if agent_orchestrator.is_running:
            return {
                "success": True,
                "message": "Agent sistemi zaten çalışıyor"
            }
        
        await agent_orchestrator.start()
        
        return {
            "success": True,
            "message": "Agent sistemi başarıyla başlatıldı"
        }
        
    except Exception as e:
        logger.error(f"Agent sistem başlatma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/stop")
async def stop_agent_system():
    """Agent sistemini durdur (admin only)"""
    try:
        if not agent_orchestrator.is_running:
            return {
                "success": True,
                "message": "Agent sistemi zaten durmuş"
            }
        
        await agent_orchestrator.stop()
        
        return {
            "success": True,
            "message": "Agent sistemi başarıyla durduruldu"
        }
        
    except Exception as e:
        logger.error(f"Agent sistem durdurma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/stats")
async def get_mcp_stats():
    """MCP (Model Context Protocol) istatistikleri"""
    try:
        from app.services.mcp_service import mcp_service
        
        stats = await mcp_service.get_service_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"MCP istatistikleri alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/a2a/stats")
async def get_a2a_stats():
    """A2A (Agent-to-Agent) network istatistikleri"""
    try:
        from app.services.a2a_network import a2a_network
        
        stats = await a2a_network.get_network_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"A2A istatistikleri alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/list")
async def list_active_agents():
    """Aktif agent'ları listele"""
    try:
        from app.services.mcp_service import mcp_service
        
        active_agents = await mcp_service.context_store.get_active_agents()
        
        agents_info = []
        for agent in active_agents:
            agents_info.append({
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
                "capabilities": agent.capabilities,
                "status": agent.status,
                "current_tasks": agent.current_tasks,
                "last_seen": agent.last_seen.isoformat(),
                "metadata": agent.metadata
            })
        
        return {
            "success": True,
            "data": {
                "total_agents": len(agents_info),
                "agents": agents_info
            }
        }
        
    except Exception as e:
        logger.error(f"Agent listesi alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/active")
async def get_active_workflows():
    """Aktif workflow'ları listele"""
    try:
        if not agent_orchestrator.is_running:
            raise HTTPException(
                status_code=503, 
                detail="Agent sistemi çalışmıyor"
            )
        
        coordinator = agent_orchestrator.agents.get("coordinator_agent_001")
        if not coordinator:
            raise HTTPException(
                status_code=503, 
                detail="Coordinator Agent bulunamadı"
            )
        
        workflows = []
        for workflow_id, workflow_data in coordinator.active_workflows.items():
            workflows.append({
                "workflow_id": workflow_id,
                "workflow_type": workflow_data["workflow_type"],
                "status": workflow_data["status"],
                "created_at": workflow_data["created_at"].isoformat(),
                "tasks_count": len(workflow_data.get("tasks", {})),
                "progress": workflow_data.get("progress", 0)
            })
        
        return {
            "success": True,
            "data": {
                "total_workflows": len(workflows),
                "workflows": workflows
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow listesi alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 