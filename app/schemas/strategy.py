"""
Strategy Schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class StrategyBase(BaseModel):
    """Strateji temel şeması"""
    title: Optional[str] = None
    content: Optional[str] = None
    market_analysis: Optional[Dict[str, Any]] = None
    customer_segments: Optional[Dict[str, Any]] = None
    pricing_recommendations: Optional[Dict[str, Any]] = None
    messaging_content: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)
    expected_roi: Optional[float] = Field(default=None, ge=0)
    implementation_difficulty: Optional[str] = Field(default=None)


class StrategyCreate(StrategyBase):
    """Strateji oluşturma şeması"""
    product_id: int


class StrategyResponse(StrategyBase):
    """Strateji yanıt şeması"""
    id: int
    user_id: int
    product_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PerformanceDataBase(BaseModel):
    """Performans verisi temel şeması"""
    sales_amount: float = Field(ge=0)
    units_sold: int = Field(ge=0)
    conversion_rate: Optional[float] = Field(default=None, ge=0, le=1)
    customer_acquisition_cost: Optional[float] = Field(default=None, ge=0)
    roi: Optional[float] = Field(default=None)
    period_start: datetime
    period_end: datetime


class PerformanceDataCreate(PerformanceDataBase):
    """Performans verisi oluşturma şeması"""
    product_id: int
    strategy_id: Optional[int] = None


class PerformanceDataResponse(PerformanceDataBase):
    """Performans verisi yanıt şeması"""
    id: int
    product_id: int
    strategy_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 