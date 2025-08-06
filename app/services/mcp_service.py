"""
MCP (Model Context Protocol) Service
Agent'lar arası context paylaşımı ve iletişim protokolü
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MCPMessageType(Enum):
    """MCP mesaj türleri"""
    CONTEXT_SHARE = "context_share"
    CONTEXT_REQUEST = "context_request"
    CONTEXT_UPDATE = "context_update"
    AGENT_REGISTER = "agent_register"
    AGENT_STATUS = "agent_status"
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    COORDINATION = "coordination"

@dataclass
class MCPMessage:
    """MCP mesaj yapısı"""
    id: str
    type: MCPMessageType
    sender_id: str
    receiver_id: Optional[str]  # None = broadcast
    payload: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    priority: int = 1  # 1=low, 2=medium, 3=high
    
    def to_dict(self) -> Dict[str, Any]:
        """Mesajı dict'e çevir"""
        data = asdict(self)
        data['type'] = self.type.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Dict'ten mesaj oluştur"""
        data['type'] = MCPMessageType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)

@dataclass
class AgentContext:
    """Agent context bilgisi"""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    current_tasks: List[str]
    status: str  # "active", "busy", "idle", "offline"
    last_seen: datetime
    metadata: Dict[str, Any]

class MCPContextStore:
    """MCP Context Store - Agent'lar arası context paylaşımı"""
    
    def __init__(self):
        self.contexts: Dict[str, AgentContext] = {}
        self.shared_data: Dict[str, Any] = {}
        self.message_queue: List[MCPMessage] = []
        self.subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    async def register_agent(self, agent_context: AgentContext) -> bool:
        """Agent'ı sisteme kaydet"""
        async with self._lock:
            self.contexts[agent_context.agent_id] = agent_context
            logger.info(f"🤖 Agent kaydedildi: {agent_context.agent_id} ({agent_context.agent_type})")
            
            # Kayıt mesajı gönder
            await self._broadcast_message(MCPMessage(
                id=str(uuid.uuid4()),
                type=MCPMessageType.AGENT_REGISTER,
                sender_id=agent_context.agent_id,
                receiver_id=None,
                payload={
                    "agent_type": agent_context.agent_type,
                    "capabilities": agent_context.capabilities,
                    "status": agent_context.status
                },
                timestamp=datetime.now()
            ))
            
            return True
    
    async def update_agent_status(self, agent_id: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """Agent durumunu güncelle"""
        async with self._lock:
            if agent_id in self.contexts:
                self.contexts[agent_id].status = status
                self.contexts[agent_id].last_seen = datetime.now()
                if metadata:
                    self.contexts[agent_id].metadata.update(metadata)
                
                # Durum güncellemesi mesajı
                await self._broadcast_message(MCPMessage(
                    id=str(uuid.uuid4()),
                    type=MCPMessageType.AGENT_STATUS,
                    sender_id=agent_id,
                    receiver_id=None,
                    payload={
                        "status": status,
                        "metadata": metadata or {}
                    },
                    timestamp=datetime.now()
                ))
                
                return True
            return False
    
    async def share_context(self, sender_id: str, context_key: str, context_data: Any, ttl_minutes: int = 60) -> bool:
        """Context paylaş"""
        async with self._lock:
            expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
            
            self.shared_data[context_key] = {
                "data": context_data,
                "sender_id": sender_id,
                "created_at": datetime.now(),
                "expires_at": expires_at
            }
            
            # Context paylaşım mesajı
            await self._broadcast_message(MCPMessage(
                id=str(uuid.uuid4()),
                type=MCPMessageType.CONTEXT_SHARE,
                sender_id=sender_id,
                receiver_id=None,
                payload={
                    "context_key": context_key,
                    "context_type": type(context_data).__name__,
                    "expires_at": expires_at.isoformat()
                },
                timestamp=datetime.now()
            ))
            
            return True
    
    async def get_context(self, context_key: str) -> Optional[Any]:
        """Context al"""
        async with self._lock:
            if context_key in self.shared_data:
                context_info = self.shared_data[context_key]
                
                # Süre kontrolü
                if context_info["expires_at"] > datetime.now():
                    return context_info["data"]
                else:
                    # Süresi dolmuş context'i temizle
                    del self.shared_data[context_key]
            
            return None
    
    async def send_message(self, message: MCPMessage) -> bool:
        """Mesaj gönder"""
        async with self._lock:
            self.message_queue.append(message)
            
            # Subscriber'lara bildir
            if message.receiver_id:
                # Belirli bir agent'a
                if message.receiver_id in self.subscribers:
                    for callback in self.subscribers[message.receiver_id]:
                        try:
                            await callback(message)
                        except Exception as e:
                            logger.error(f"❌ Callback hatası: {e}")
            else:
                # Broadcast
                await self._broadcast_message(message)
            
            return True
    
    async def _broadcast_message(self, message: MCPMessage):
        """Mesajı tüm subscriber'lara gönder"""
        for agent_id, callbacks in self.subscribers.items():
            if agent_id != message.sender_id:  # Gönderene geri gönderme
                for callback in callbacks:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"❌ Broadcast callback hatası: {e}")
    
    async def subscribe(self, agent_id: str, callback: Callable[[MCPMessage], None]):
        """Mesajlara abone ol"""
        async with self._lock:
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = []
            self.subscribers[agent_id].append(callback)
    
    async def get_active_agents(self) -> List[AgentContext]:
        """Aktif agent'ları listele"""
        async with self._lock:
            active_agents = []
            cutoff_time = datetime.now() - timedelta(minutes=5)  # 5 dakika timeout
            
            for agent_context in self.contexts.values():
                if (agent_context.status in ["active", "busy", "idle"] and 
                    agent_context.last_seen > cutoff_time):
                    active_agents.append(agent_context)
            
            return active_agents
    
    async def cleanup_expired(self):
        """Süresi dolmuş verileri temizle"""
        async with self._lock:
            now = datetime.now()
            
            # Süresi dolmuş context'leri temizle
            expired_keys = [
                key for key, value in self.shared_data.items()
                if value["expires_at"] < now
            ]
            
            for key in expired_keys:
                del self.shared_data[key]
            
            # Süresi dolmuş mesajları temizle
            self.message_queue = [
                msg for msg in self.message_queue
                if not msg.expires_at or msg.expires_at > now
            ]
            
            if expired_keys:
                logger.info(f"🧹 {len(expired_keys)} süresi dolmuş context temizlendi")

class MCPService:
    """MCP Ana Servisi"""
    
    def __init__(self):
        self.context_store = MCPContextStore()
        self.is_running = False
        self._cleanup_task = None
    
    async def start(self):
        """MCP servisini başlat"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Periyodik temizlik görevi başlat
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("🚀 MCP Service başlatıldı")
    
    async def stop(self):
        """MCP servisini durdur"""
        self.is_running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 MCP Service durduruldu")
    
    async def _periodic_cleanup(self):
        """Periyodik temizlik görevi"""
        while self.is_running:
            try:
                await self.context_store.cleanup_expired()
                await asyncio.sleep(300)  # 5 dakikada bir temizlik
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Temizlik hatası: {e}")
                await asyncio.sleep(60)
    
    async def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> bool:
        """Agent kaydet"""
        agent_context = AgentContext(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            current_tasks=[],
            status="active",
            last_seen=datetime.now(),
            metadata={}
        )
        
        return await self.context_store.register_agent(agent_context)
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """MCP servis istatistikleri"""
        active_agents = await self.context_store.get_active_agents()
        
        return {
            "active_agents": len(active_agents),
            "total_contexts": len(self.context_store.contexts),
            "shared_data_count": len(self.context_store.shared_data),
            "message_queue_size": len(self.context_store.message_queue),
            "agents_by_type": {},
            "service_uptime": "running" if self.is_running else "stopped"
        }

# Global MCP Service instance
mcp_service = MCPService() 