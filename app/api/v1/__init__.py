"""
API v1 Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, products, strategies, users, performance, rag, agents, pdf_documents

api_router = APIRouter()

# Endpoint'leri dahil et
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag-vector-search"])
api_router.include_router(agents.router, prefix="/agents", tags=["agent-systems"])
api_router.include_router(pdf_documents.router, prefix="/pdf", tags=["pdf-documents"]) 