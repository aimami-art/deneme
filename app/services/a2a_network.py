"""
A2A (Agent-to-Agent) Network Service
Agent'lar arası doğrudan iletişim ve koordinasyon ağı
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import weakref

from app.services.mcp_service import mcp_service, MCPMessage, MCPMessageType

logger = logging.getLogger(__name__)

class A2ATaskType(Enum):
    """A2A görev türleri"""
    MARKET_ANALYSIS = "market_analysis"
    STRATEGY_GENERATION = "strategy_generation"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPETITOR_RESEARCH = "competitor_research"
    PRICE_OPTIMIZATION = "price_optimization"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    COORDINATION = "coordination"

class A2ATaskStatus(Enum):
    """A2A görev durumları"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class A2ATask:
    """A2A görev yapısı"""
    task_id: str
    task_type: A2ATaskType
    requester_id: str
    assignee_id: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high
    status: A2ATaskStatus = A2ATaskStatus.PENDING
    input_data: Dict[str, Any] = None
    output_data: Dict[str, Any] = None
    created_at: datetime = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    dependencies: List[str] = None  # Bağımlı görev ID'leri
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.input_data is None:
            self.input_data = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}

class A2AAgent:
    """A2A Agent base class"""
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.status = "idle"
        self.current_tasks: Set[str] = set()
        self.max_concurrent_tasks = 3
        self.network: Optional['A2ANetwork'] = None
        self._message_handlers: Dict[MCPMessageType, Callable] = {}
        
        # MCP message handler'larını kaydet
        self._register_message_handlers()
    
    def _register_message_handlers(self):
        """MCP mesaj handler'larını kaydet"""
        self._message_handlers = {
            MCPMessageType.TASK_ASSIGN: self._handle_task_assignment,
            MCPMessageType.CONTEXT_SHARE: self._handle_context_share,
            MCPMessageType.COORDINATION: self._handle_coordination,
        }
    
    async def join_network(self, network: 'A2ANetwork'):
        """A2A ağına katıl"""
        self.network = network
        await network.register_agent(self)
        
        # MCP sistemine kaydol
        await mcp_service.register_agent(self.agent_id, self.agent_type, self.capabilities)
        
        # MCP mesajlarına abone ol
        await mcp_service.context_store.subscribe(self.agent_id, self._handle_mcp_message)
        
        logger.info(f"🤖 Agent {self.agent_id} A2A ağına katıldı")
    
    async def _handle_mcp_message(self, message: MCPMessage):
        """MCP mesajını işle"""
        if message.type in self._message_handlers:
            try:
                await self._message_handlers[message.type](message)
            except Exception as e:
                logger.error(f"❌ {self.agent_id} mesaj işleme hatası: {e}")
    
    async def _handle_task_assignment(self, message: MCPMessage):
        """Görev atama mesajını işle"""
        task_data = message.payload
        task_id = task_data.get("task_id")
        
        if task_id and len(self.current_tasks) < self.max_concurrent_tasks:
            # Görevi kabul et
            await self._accept_task(task_id)
        else:
            # Görevi reddet
            await self._reject_task(task_id, "Agent meşgul veya kapasite dolu")
    
    async def _handle_context_share(self, message: MCPMessage):
        """Context paylaşım mesajını işle"""
        context_key = message.payload.get("context_key")
        logger.info(f"📡 {self.agent_id} yeni context aldı: {context_key}")
    
    async def _handle_coordination(self, message: MCPMessage):
        """Koordinasyon mesajını işle"""
        coordination_type = message.payload.get("type")
        logger.info(f"🎯 {self.agent_id} koordinasyon mesajı: {coordination_type}")
    
    async def _accept_task(self, task_id: str):
        """Görevi kabul et"""
        if self.network:
            task = await self.network.get_task(task_id)
            if task and task.status == A2ATaskStatus.PENDING:
                self.current_tasks.add(task_id)
                self.status = "busy"
                
                # Görevi başlat
                await self.network.update_task_status(task_id, A2ATaskStatus.IN_PROGRESS, self.agent_id)
                
                # Asenkron olarak görevi işle
                asyncio.create_task(self._execute_task(task))
    
    async def _reject_task(self, task_id: str, reason: str):
        """Görevi reddet"""
        logger.info(f"❌ {self.agent_id} görevi reddetti: {task_id} - {reason}")
    
    async def _execute_task(self, task: A2ATask):
        """Görevi çalıştır (alt sınıflar override etmeli)"""
        try:
            # Varsayılan implementasyon
            await asyncio.sleep(2)  # Simüle edilmiş işlem
            
            result = {
                "status": "completed",
                "message": f"{self.agent_type} tarafından işlendi",
                "processed_at": datetime.now().isoformat()
            }
            
            await self._complete_task(task.task_id, result)
            
        except Exception as e:
            await self._fail_task(task.task_id, str(e))
    
    async def _complete_task(self, task_id: str, result: Dict[str, Any]):
        """Görevi tamamla"""
        if self.network:
            await self.network.complete_task(task_id, result)
        
        self.current_tasks.discard(task_id)
        if not self.current_tasks:
            self.status = "idle"
    
    async def _fail_task(self, task_id: str, error: str):
        """Görevi başarısız olarak işaretle"""
        if self.network:
            await self.network.fail_task(task_id, error)
        
        self.current_tasks.discard(task_id)
        if not self.current_tasks:
            self.status = "idle"
    
    async def request_task(self, task_type: A2ATaskType, input_data: Dict[str, Any], 
                          priority: int = 1, deadline: Optional[datetime] = None) -> str:
        """Yeni görev talep et"""
        if not self.network:
            raise ValueError("Agent ağa bağlı değil")
        
        task = A2ATask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            requester_id=self.agent_id,
            priority=priority,
            input_data=input_data,
            deadline=deadline
        )
        
        return await self.network.submit_task(task)
    
    def can_handle_task(self, task_type: A2ATaskType) -> bool:
        """Bu görevi işleyebilir mi?"""
        return task_type.value in [cap.lower() for cap in self.capabilities]

class A2ANetwork:
    """A2A Network - Agent'lar arası koordinasyon ağı"""
    
    def __init__(self):
        self.agents: Dict[str, A2AAgent] = {}
        self.tasks: Dict[str, A2ATask] = {}
        self.task_queue: List[str] = []  # Bekleyen görevler
        self._lock = asyncio.Lock()
        self.is_running = False
        self._scheduler_task = None
    
    async def start(self):
        """A2A ağını başlat"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Görev zamanlayıcısını başlat
        self._scheduler_task = asyncio.create_task(self._task_scheduler())
        
        logger.info("🌐 A2A Network başlatıldı")
    
    async def stop(self):
        """A2A ağını durdur"""
        self.is_running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 A2A Network durduruldu")
    
    async def register_agent(self, agent: A2AAgent):
        """Agent'ı ağa kaydet"""
        async with self._lock:
            self.agents[agent.agent_id] = agent
            logger.info(f"🤖 Agent kaydedildi: {agent.agent_id} ({agent.agent_type})")
    
    async def submit_task(self, task: A2ATask) -> str:
        """Yeni görev gönder"""
        async with self._lock:
            self.tasks[task.task_id] = task
            self.task_queue.append(task.task_id)
            
            # Önceliğe göre sırala
            self.task_queue.sort(key=lambda tid: self.tasks[tid].priority, reverse=True)
            
            logger.info(f"📋 Yeni görev eklendi: {task.task_id} ({task.task_type.value})")
            
            return task.task_id
    
    async def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Görev bilgisi al"""
        return self.tasks.get(task_id)
    
    async def update_task_status(self, task_id: str, status: A2ATaskStatus, assignee_id: str = None):
        """Görev durumunu güncelle"""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                
                if assignee_id:
                    task.assignee_id = assignee_id
                    task.assigned_at = datetime.now()
                
                if status == A2ATaskStatus.IN_PROGRESS:
                    # Kuyruktan çıkar
                    if task_id in self.task_queue:
                        self.task_queue.remove(task_id)
    
    async def complete_task(self, task_id: str, result: Dict[str, Any]):
        """Görevi tamamla"""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = A2ATaskStatus.COMPLETED
                task.output_data = result
                task.completed_at = datetime.now()
                
                logger.info(f"✅ Görev tamamlandı: {task_id}")
                
                # Context'i paylaş
                await mcp_service.context_store.share_context(
                    sender_id=task.assignee_id,
                    context_key=f"task_result_{task_id}",
                    context_data=result,
                    ttl_minutes=120
                )
    
    async def fail_task(self, task_id: str, error: str):
        """Görevi başarısız olarak işaretle"""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = A2ATaskStatus.FAILED
                task.metadata["error"] = error
                task.completed_at = datetime.now()
                
                logger.error(f"❌ Görev başarısız: {task_id} - {error}")
    
    async def _task_scheduler(self):
        """Görev zamanlayıcısı"""
        while self.is_running:
            try:
                await self._assign_pending_tasks()
                await asyncio.sleep(5)  # 5 saniyede bir kontrol
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Scheduler hatası: {e}")
                await asyncio.sleep(10)
    
    async def _assign_pending_tasks(self):
        """Bekleyen görevleri ata"""
        async with self._lock:
            if not self.task_queue:
                return
            
            # En yüksek öncelikli görevi al
            task_id = self.task_queue[0]
            task = self.tasks[task_id]
            
            # Uygun agent bul
            suitable_agents = [
                agent for agent in self.agents.values()
                if (agent.can_handle_task(task.task_type) and 
                    len(agent.current_tasks) < agent.max_concurrent_tasks and
                    agent.status != "offline")
            ]
            
            if suitable_agents:
                # En az meşgul olan agent'ı seç
                selected_agent = min(suitable_agents, key=lambda a: len(a.current_tasks))
                
                # Görev atama mesajı gönder
                message = MCPMessage(
                    id=str(uuid.uuid4()),
                    type=MCPMessageType.TASK_ASSIGN,
                    sender_id="a2a_network",
                    receiver_id=selected_agent.agent_id,
                    payload={
                        "task_id": task_id,
                        "task_type": task.task_type.value,
                        "input_data": task.input_data,
                        "priority": task.priority,
                        "deadline": task.deadline.isoformat() if task.deadline else None
                    },
                    timestamp=datetime.now()
                )
                
                await mcp_service.context_store.send_message(message)
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Ağ istatistikleri"""
        active_agents = len([a for a in self.agents.values() if a.status != "offline"])
        
        task_stats = {}
        for status in A2ATaskStatus:
            task_stats[status.value] = len([t for t in self.tasks.values() if t.status == status])
        
        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "total_tasks": len(self.tasks),
            "pending_tasks": len(self.task_queue),
            "task_stats": task_stats,
            "network_status": "running" if self.is_running else "stopped"
        }

# Global A2A Network instance
a2a_network = A2ANetwork() 