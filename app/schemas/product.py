"""
Product Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ProductCategoryBase(BaseModel):
    """Ürün kategori temel şeması"""
    name: str
    description: Optional[str] = None


class ProductCategoryCreate(ProductCategoryBase):
    """Ürün kategori oluşturma şeması"""
    pass


class ProductCategoryResponse(ProductCategoryBase):
    """Ürün kategori yanıt şeması"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Ürün temel şeması"""
    name: str
    description: str
    category: str
    cost_price: float = Field(gt=0)
    target_profit_margin: Optional[float] = Field(default=None, ge=0)


class ProductCreate(ProductBase):
    """Ürün oluşturma şeması"""
    pass


class ProductResponse(ProductBase):
    """Ürün yanıt şeması"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 