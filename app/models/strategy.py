"""
Strateji Modeli
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Strategy(Base):
    """Strateji tablosu"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # AI Analiz Sonuçları
    market_analysis = Column(JSON, nullable=True)  # MarketAnalyzer çıktısı
    customer_segments = Column(JSON, nullable=True)  # CustomerSegmenter çıktısı
    pricing_recommendations = Column(JSON, nullable=True)  # PricingAdvisor çıktısı
    messaging_content = Column(JSON, nullable=True)  # MessagingGenerator çıktısı
    
    # Strateji Metrikleri
    confidence_score = Column(Float, nullable=True)
    expected_roi = Column(Float, nullable=True)
    implementation_difficulty = Column(String, nullable=True)  # easy, medium, hard
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # İlişkiler
    user = relationship("User", back_populates="strategies")
    product = relationship("Product", back_populates="strategies")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, title='{self.title}')>"


class PerformanceData(Base):
    """Performans takip tablosu"""
    __tablename__ = "performance_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_amount = Column(Float, nullable=False)
    units_sold = Column(Integer, nullable=False)
    conversion_rate = Column(Float, nullable=True)
    customer_acquisition_cost = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    
    # Zaman bilgisi
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    
    # İlişkiler
    product = relationship("Product", back_populates="performance_data")
    
    def __repr__(self):
        return f"<PerformanceData(id={self.id}, sales_amount={self.sales_amount})>" 