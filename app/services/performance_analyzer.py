"""
Performans Analizi ve Strateji Önerisi Servisi
Satış performans verilerini analiz ederek AI destekli yeni stratejiler önerir
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

import google.generativeai as genai

from app.core.config import settings
from app.models.strategy import PerformanceData, Strategy
from app.models.product import Product
from app.services.ai_services import AIServiceBase


class PerformanceAnalyzer(AIServiceBase):
    """Performans verilerini analiz eden ve strateji öneren AI modülü"""
    
    def __init__(self):
        super().__init__()
    
    async def analyze_performance_and_suggest_strategies(
        self, 
        product_id: int, 
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Ürün performansını analiz et ve yeni stratejiler öner"""
        try:
            # Ürün bilgilerini al
            product = db.query(Product).filter(
                Product.id == product_id,
                Product.owner_id == user_id
            ).first()
            
            if not product:
                return {"error": "Ürün bulunamadı"}
            
            # Performans verilerini al
            performance_data = await self._get_performance_data(product_id, db)
            
            if not performance_data:
                return {"error": "Performans verisi bulunamadı"}
            
            # Performans analizi yap
            performance_analysis = await self._analyze_performance_trends(performance_data)
            
            # Mevcut stratejileri al
            existing_strategies = await self._get_existing_strategies(product_id, db)
            
            # AI ile yeni strateji önerileri oluştur
            strategy_recommendations = await self._generate_performance_based_strategies(
                product, performance_analysis, existing_strategies
            )
            
            # Performans karşılaştırması yap
            performance_comparison = await self._compare_strategy_performance(
                product_id, db
            )
            
            return {
                "product_name": product.name,
                "performance_summary": performance_analysis,
                "strategy_recommendations": strategy_recommendations,
                "performance_comparison": performance_comparison,
                "analysis_timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Performans analizi hatası: {e}")
            return {
                "error": f"Performans analizi sırasında hata oluştu: {str(e)}",
                "success": False
            }
    
    async def _get_performance_data(self, product_id: int, db: Session) -> List[PerformanceData]:
        """Ürünün performans verilerini getir"""
        return db.query(PerformanceData).filter(
            PerformanceData.product_id == product_id
        ).order_by(desc(PerformanceData.period_start)).limit(20).all()
    
    async def _get_existing_strategies(self, product_id: int, db: Session) -> List[Strategy]:
        """Mevcut stratejileri getir"""
        return db.query(Strategy).filter(
            Strategy.product_id == product_id
        ).order_by(desc(Strategy.created_at)).limit(5).all()
    
    async def _analyze_performance_trends(self, performance_data: List[PerformanceData]) -> Dict[str, Any]:
        """Performans trendlerini analiz et"""
        if not performance_data:
            return {}
        
        # Temel istatistikler
        total_sales = sum(p.sales_amount for p in performance_data)
        total_units = sum(p.units_sold for p in performance_data)
        avg_conversion = sum(p.conversion_rate or 0 for p in performance_data) / len(performance_data)
        avg_roi = sum(p.roi or 0 for p in performance_data) / len(performance_data)
        
        # Trend analizi (son 3 vs önceki 3 dönem)
        recent_data = performance_data[:3] if len(performance_data) >= 3 else performance_data
        older_data = performance_data[3:6] if len(performance_data) >= 6 else []
        
        trend_analysis = {}
        if older_data:
            recent_avg_sales = sum(p.sales_amount for p in recent_data) / len(recent_data)
            older_avg_sales = sum(p.sales_amount for p in older_data) / len(older_data)
            sales_trend = ((recent_avg_sales - older_avg_sales) / older_avg_sales) * 100 if older_avg_sales > 0 else 0
            
            recent_avg_roi = sum(p.roi or 0 for p in recent_data) / len(recent_data)
            older_avg_roi = sum(p.roi or 0 for p in older_data) / len(older_data)
            roi_trend = recent_avg_roi - older_avg_roi
            
            trend_analysis = {
                "sales_trend_percent": round(sales_trend, 2),
                "roi_trend_percent": round(roi_trend, 2),
                "trend_direction": "yükseliş" if sales_trend > 5 else "düşüş" if sales_trend < -5 else "stabil"
            }
        
        # Performans kategorisi belirleme
        performance_category = self._categorize_performance(avg_roi, avg_conversion, total_sales)
        
        # Sorunlu alanları tespit et
        problem_areas = self._identify_problem_areas(performance_data)
        
        # Fırsatları tespit et
        opportunities = self._identify_opportunities(performance_data, trend_analysis)
        
        return {
            "total_sales": round(total_sales, 2),
            "total_units": total_units,
            "average_conversion_rate": round(avg_conversion * 100, 2),
            "average_roi": round(avg_roi, 2),
            "performance_category": performance_category,
            "trend_analysis": trend_analysis,
            "problem_areas": problem_areas,
            "opportunities": opportunities,
            "data_points": len(performance_data)
        }
    
    def _categorize_performance(self, avg_roi: float, avg_conversion: float, total_sales: float) -> str:
        """Performans kategorisini belirle"""
        if avg_roi > 20 and avg_conversion > 0.05 and total_sales > 10000:
            return "mükemmel"
        elif avg_roi > 10 and avg_conversion > 0.03:
            return "iyi"
        elif avg_roi > 5 and avg_conversion > 0.02:
            return "orta"
        else:
            return "zayıf"
    
    def _identify_problem_areas(self, performance_data: List[PerformanceData]) -> List[str]:
        """Sorunlu alanları tespit et"""
        problems = []
        
        # Düşük dönüşüm oranı
        avg_conversion = sum(p.conversion_rate or 0 for p in performance_data) / len(performance_data)
        if avg_conversion < 0.02:
            problems.append("Düşük dönüşüm oranı")
        
        # Yüksek müşteri edinme maliyeti
        avg_cac = sum(p.customer_acquisition_cost or 0 for p in performance_data) / len(performance_data)
        avg_sales = sum(p.sales_amount for p in performance_data) / len(performance_data)
        if avg_cac > 0 and avg_sales > 0 and (avg_cac / avg_sales) > 0.3:
            problems.append("Yüksek müşteri edinme maliyeti")
        
        # Düşük ROI
        avg_roi = sum(p.roi or 0 for p in performance_data) / len(performance_data)
        if avg_roi < 5:
            problems.append("Düşük yatırım getirisi")
        
        # Satış düşüşü trendi
        if len(performance_data) >= 3:
            recent_sales = sum(p.sales_amount for p in performance_data[:3])
            if len(performance_data) >= 6:
                older_sales = sum(p.sales_amount for p in performance_data[3:6])
                if recent_sales < older_sales * 0.9:
                    problems.append("Satış düşüş trendi")
        
        return problems
    
    def _identify_opportunities(self, performance_data: List[PerformanceData], trend_analysis: Dict) -> List[str]:
        """Fırsatları tespit et"""
        opportunities = []
        
        # Pozitif trend
        if trend_analysis.get("sales_trend_percent", 0) > 10:
            opportunities.append("Güçlü satış momentum'u")
        
        # Yüksek ROI potansiyeli
        avg_roi = sum(p.roi or 0 for p in performance_data) / len(performance_data)
        if avg_roi > 15:
            opportunities.append("Yüksek karlılık potansiyeli")
        
        # İyi dönüşüm oranı
        avg_conversion = sum(p.conversion_rate or 0 for p in performance_data) / len(performance_data)
        if avg_conversion > 0.05:
            opportunities.append("Güçlü müşteri ilgisi")
        
        # Büyüme potansiyeli
        if len(performance_data) >= 2:
            latest_units = performance_data[0].units_sold
            if latest_units > 50:
                opportunities.append("Ölçeklendirme potansiyeli")
        
        return opportunities
    
    async def _compare_strategy_performance(self, product_id: int, db: Session) -> Dict[str, Any]:
        """Strateji performanslarını karşılaştır"""
        try:
            # Stratejilere göre performans verilerini grupla
            strategy_performance = db.query(
                PerformanceData.strategy_id,
                func.avg(PerformanceData.sales_amount).label('avg_sales'),
                func.avg(PerformanceData.roi).label('avg_roi'),
                func.avg(PerformanceData.conversion_rate).label('avg_conversion'),
                func.count(PerformanceData.id).label('data_count')
            ).filter(
                PerformanceData.product_id == product_id,
                PerformanceData.strategy_id.isnot(None)
            ).group_by(PerformanceData.strategy_id).all()
            
            # Strateji bilgilerini al
            strategy_comparisons = []
            for perf in strategy_performance:
                strategy = db.query(Strategy).filter(Strategy.id == perf.strategy_id).first()
                if strategy:
                    strategy_comparisons.append({
                        "strategy_id": perf.strategy_id,
                        "strategy_title": strategy.title,
                        "avg_sales": round(float(perf.avg_sales or 0), 2),
                        "avg_roi": round(float(perf.avg_roi or 0), 2),
                        "avg_conversion": round(float(perf.avg_conversion or 0) * 100, 2),
                        "data_points": perf.data_count
                    })
            
            # En iyi performans gösteren stratejiyi bul
            best_strategy = None
            if strategy_comparisons:
                best_strategy = max(strategy_comparisons, key=lambda x: x['avg_roi'])
            
            return {
                "strategy_comparisons": strategy_comparisons,
                "best_performing_strategy": best_strategy,
                "total_strategies_analyzed": len(strategy_comparisons)
            }
            
        except Exception as e:
            print(f"❌ Strateji karşılaştırma hatası: {e}")
            return {"error": "Strateji karşılaştırması yapılamadı"}
    
    async def _generate_performance_based_strategies(
        self, 
        product: Product, 
        performance_analysis: Dict, 
        existing_strategies: List[Strategy]
    ) -> List[Dict[str, Any]]:
        """Performans verilerine dayalı yeni stratejiler oluştur"""
        try:
            # Mevcut stratejilerin özetini çıkar
            existing_strategy_summary = ""
            if existing_strategies:
                existing_strategy_summary = "\n".join([
                    f"- {strategy.title}: {strategy.content[:100]}..."
                    for strategy in existing_strategies[:3]
                ])
            
            prompt = f"""
            Ürün: {product.name}
            Kategori: {product.category}
            Maliyet: {product.cost_price} TL
            
            PERFORMANS ANALİZİ:
            - Toplam Satış: {performance_analysis.get('total_sales', 0)} TL
            - Ortalama ROI: {performance_analysis.get('average_roi', 0)}%
            - Dönüşüm Oranı: {performance_analysis.get('average_conversion_rate', 0)}%
            - Performans Kategorisi: {performance_analysis.get('performance_category', 'bilinmiyor')}
            - Trend: {performance_analysis.get('trend_analysis', {}).get('trend_direction', 'stabil')}
            
            SORUNLU ALANLAR:
            {chr(10).join(f"- {problem}" for problem in performance_analysis.get('problem_areas', []))}
            
            FIRSATLAR:
            {chr(10).join(f"- {opp}" for opp in performance_analysis.get('opportunities', []))}
            
            MEVCUT STRATEJİLER:
            {existing_strategy_summary}
            
            Bu performans verilerine dayanarak, ürünün satış performansını artırmak için 3 yeni strateji öner.
            Her strateji için:
            1. Strateji başlığı
            2. Detaylı açıklama (en az 200 kelime)
            3. Beklenen ROI tahmini
            4. Uygulama zorluğu (kolay/orta/zor)
            5. Odaklandığı sorunlu alan
            
            Stratejiler performans verilerindeki sorunları çözmeli ve fırsatları değerlendirmeli.
            Türkçe olarak, somut ve uygulanabilir öneriler sun.
            
            Yanıtını şu JSON formatında ver:
            [
                {{
                    "title": "Strateji başlığı",
                    "content": "Detaylı strateji açıklaması",
                    "expected_roi": 15.5,
                    "implementation_difficulty": "orta",
                    "target_problem": "Düşük dönüşüm oranı",
                    "key_actions": ["Eylem 1", "Eylem 2", "Eylem 3"]
                }}
            ]
            """
            
            ai_response = await self._call_gemini(prompt)
            
            # JSON yanıtını parse etmeye çalış
            try:
                import json
                # Yanıttan JSON kısmını çıkar
                json_start = ai_response.find('[')
                json_end = ai_response.rfind(']') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    strategies = json.loads(json_str)
                    return strategies
                else:
                    # JSON formatında değilse, metin olarak işle
                    return self._parse_text_strategy_response(ai_response)
                    
            except json.JSONDecodeError:
                # JSON parse edilemezse, metin olarak işle
                return self._parse_text_strategy_response(ai_response)
                
        except Exception as e:
            print(f"❌ Strateji oluşturma hatası: {e}")
            return [{
                "title": "Performans Optimizasyon Stratejisi",
                "content": f"Mevcut performans verilerine dayanarak özel bir strateji oluşturulamadı. Genel öneriler: {performance_analysis.get('problem_areas', [])}",
                "expected_roi": 10.0,
                "implementation_difficulty": "orta",
                "target_problem": "Genel performans optimizasyonu",
                "key_actions": ["Performans verilerini detaylı analiz et", "Hedef müşteri segmentini yeniden değerlendir", "Fiyatlandırma stratejisini gözden geçir"]
            }]
    
    def _parse_text_strategy_response(self, response: str) -> List[Dict[str, Any]]:
        """Metin formatındaki AI yanıtını parse et"""
        strategies = []
        
        # Basit parsing - gerçek implementasyonda daha gelişmiş olabilir
        sections = response.split('\n\n')
        
        for i, section in enumerate(sections):
            if section.strip():
                strategies.append({
                    "title": f"Performans Odaklı Strateji {i+1}",
                    "content": section.strip(),
                    "expected_roi": 12.0,
                    "implementation_difficulty": "orta",
                    "target_problem": "Performans optimizasyonu",
                    "key_actions": ["Stratejiyi uygula", "Sonuçları takip et", "Gerekirse ayarlama yap"]
                })
        
        return strategies[:3]  # En fazla 3 strateji döndür
    
    async def create_strategy_from_performance(
        self, 
        product_id: int, 
        strategy_data: Dict[str, Any], 
        db: Session, 
        user_id: int
    ) -> Strategy:
        """Performans analizinden çıkan stratejiyi veritabanına kaydet"""
        try:
            new_strategy = Strategy(
                title=strategy_data["title"],
                content=strategy_data["content"],
                confidence_score=0.85,  # Yüksek güven skoru - performans verilerine dayalı
                expected_roi=strategy_data.get("expected_roi", 10.0),
                implementation_difficulty=strategy_data.get("implementation_difficulty", "orta"),
                product_id=product_id,
                user_id=user_id,
                market_analysis={
                    "source": "performance_analysis",
                    "target_problem": strategy_data.get("target_problem"),
                    "key_actions": strategy_data.get("key_actions", []),
                    "created_from": "performance_data"
                }
            )
            
            db.add(new_strategy)
            db.commit()
            db.refresh(new_strategy)
            
            print(f"✅ Performans tabanlı strateji oluşturuldu: {new_strategy.title}")
            return new_strategy
            
        except Exception as e:
            print(f"❌ Strateji kaydetme hatası: {e}")
            db.rollback()
            raise e 