"""
AI Analiz Servisleri
Google Gemini API ve diğer veri kaynaklarını kullanarak gerçek analiz yapan modüller
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

import google.generativeai as genai
from pytrends.request import TrendReq
import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.models.product import Product
from app.services.rag_engine import RAGEmbeddingEngine


class AIServiceBase:
    """AI servislerinin temel sınıfı"""
    
    def __init__(self):
        # Gemini API'yi yapılandır
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # Yeni model adı
        else:
            self.model = None
    
    async def _call_gemini(self, prompt: str) -> str:
        """Gemini API'ye güvenli çağrı"""
        if not self.model:
            return "Gemini API anahtarı yapılandırılmamış"
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API hatası: {e}")
            return f"AI analizi sırasında hata oluştu: {str(e)}"


class MarketAnalyzer(AIServiceBase):
    """Pazar ve rekabet analizi modülü"""
    
    def __init__(self):
        super().__init__()
        
        # TrendReq başlat (proxy olmadan)
        self.pytrends = TrendReq(hl='tr-TR', tz=180)
        
        # SerpAPI servisini başlat
        from app.services.serp_service import SerpApiService
        self.serp_service = SerpApiService()
    

    
    async def analyze_market(self, product: Product) -> Dict[str, Any]:
        """Kapsamlı pazar analizi"""
        try:
            # Google Trends analizi
            trend_data = await self._get_trend_data(product.name, product.category)
            
            # Rekabet analizi (SerpAPI ile)
            competition_data = await self._analyze_competition(product.name, product.category)
            
            # Pazar büyüklüğü tahmini
            market_size = await self._estimate_market_size(product, trend_data)
            
            # Gemini ile pazar analizi
            market_analysis = await self._generate_market_insights(product, trend_data, competition_data)
            
            return {
                "market_size": market_size,
                "trend_score": trend_data.get("trend_score", 0.5),
                "competition_level": competition_data.get("competition_level", "Orta"),
                "demand_score": trend_data.get("demand_score", 0.6),
                "seasonal_trends": trend_data.get("seasonal_data", {}),
                "market_insights": market_analysis,
                "growth_potential": self._calculate_growth_potential(trend_data, competition_data),
                "entry_timing": self._suggest_entry_timing(trend_data),
                "competitor_analysis": competition_data,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Pazar analizi genel hatası: {e}")
            return self._get_fallback_market_data(product)
    
    async def _get_trend_data(self, product_name: str, category: str) -> Dict[str, Any]:
        """Google Trends verilerini al"""
        try:
            # Anahtar kelimeler
            keywords = [product_name, category, f"{product_name} satış"]
            
            # pytrends payload oluştur
            await asyncio.to_thread(
                self.pytrends.build_payload, 
                keywords, 
                cat=0, 
                timeframe='today 12-m', 
                geo='TR', 
                gprop=''
            )
            
            # Verileri al
            interest_over_time = await asyncio.to_thread(self.pytrends.interest_over_time)
            regional_interest = await asyncio.to_thread(self.pytrends.interest_by_region)
            related_queries = await asyncio.to_thread(self.pytrends.related_queries)
            
            # Analiz yap
            if not interest_over_time.empty and product_name in interest_over_time.columns:
                trend_score = interest_over_time[product_name].mean() / 100.0
                demand_score = min(1.0, trend_score * 1.2)
                seasonal_data = self._analyze_seasonality(interest_over_time, product_name)
            else:
                trend_score = 0.5
                demand_score = 0.6
                seasonal_data = {}
            
            return {
                "trend_score": trend_score,
                "demand_score": demand_score,
                "seasonal_data": seasonal_data,
                "regional_interest": regional_interest.to_dict() if not regional_interest.empty else {},
                "related_queries": related_queries
            }
                
        except Exception as e:
            print(f"⚠️ Trends veri alma hatası: {e}")
            # Fallback veri döndür
            return {"trend_score": 0.5, "demand_score": 0.6, "seasonal_data": {}}
    
    async def _analyze_competition(self, product_name: str, category: str) -> Dict[str, Any]:
        """Rekabet analizi (SerpAPI ile)"""
        try:
            print(f"🔍 SerpAPI ile rakip analizi başlatılıyor: {product_name}")
            
            # SerpAPI ile rakip analizi
            competitor_analysis = await self.serp_service.analyze_competitors(product_name, category)
            
            if competitor_analysis["success"]:
                print(f"✅ SerpAPI rakip analizi başarılı: {competitor_analysis['competitor_count']} rakip bulundu")
                
                # Rekabet skorunu hesapla
                competition_level = competitor_analysis["competition_level"]
                if competition_level == "Yüksek":
                    competition_score = np.random.uniform(0.7, 0.9)
                elif competition_level == "Orta":
                    competition_score = np.random.uniform(0.4, 0.7)
                else:
                    competition_score = np.random.uniform(0.2, 0.4)
                
                return {
                    "competition_level": competition_level,
                    "competition_score": competition_score,
                    "estimated_competitors": competitor_analysis["competitor_count"],
                    "price_range": competitor_analysis["price_analysis"],
                    "top_sellers": competitor_analysis.get("top_sellers", []),
                    "popular_features": competitor_analysis.get("popular_features", []),
                    "data_source": "SerpAPI",
                    "analysis_timestamp": competitor_analysis["timestamp"]
                }
            else:
                print(f"⚠️ SerpAPI başarısız, fallback kullanılıyor")
                return self._get_fallback_competition_data(product_name)
                
        except Exception as e:
            print(f"❌ Rekabet analizi hatası: {e}")
            return self._get_fallback_competition_data(product_name)
    
    def _get_fallback_competition_data(self, product_name: str) -> Dict[str, Any]:
        """Fallback rekabet verisi"""
        competition_score = np.random.uniform(0.3, 0.8)
        competition_level = "Düşük" if competition_score < 0.4 else "Orta" if competition_score < 0.7 else "Yüksek"
        
        return {
            "competition_level": competition_level,
            "competition_score": competition_score,
            "estimated_competitors": int(competition_score * 50),
            "price_range": {
                "min_price": 50,
                "max_price": 500,
                "avg_price": 200,
                "price_range": 450
            },
            "top_sellers": [],
            "popular_features": [],
            "data_source": "Fallback",
            "analysis_timestamp": datetime.now().isoformat(),
            "note": "API bağlantısı kurulamadı, tahmini veriler kullanılıyor"
        }
    
    async def _estimate_market_size(self, product: Product, trend_data: Dict) -> str:
        """Pazar büyüklüğü tahmini"""
        trend_score = trend_data.get("trend_score", 0.5)
        
        if trend_score > 0.7:
            return "Büyük"
        elif trend_score > 0.4:
            return "Orta"
        else:
            return "Küçük"
    
    async def _generate_market_insights(self, product: Product, trend_data: Dict, competition_data: Dict) -> str:
        """Gemini ile pazar içgörüleri oluştur"""
        prompt = f"""
        Ürün: {product.name}
        Kategori: {product.category}
        Açıklama: {product.description}
        Maliyet: {product.cost_price} TL
        
        Trend Skoru: {trend_data.get('trend_score')}
        Talep Skoru: {trend_data.get('demand_score')}
        Rekabet Seviyesi: {competition_data.get('competition_level')}
        Rakip Sayısı: {competition_data.get('estimated_competitors')}
        
        Bu ürün için Türkiye pazarında detaylı pazar analizi yap. Şu konulara odaklan:
        1. Pazar fırsatları ve tehditler
        2. Hedef müşteri profili
        3. Pazara giriş stratejisi
        4. Rekabet avantajları
        5. Büyüme potansiyeli
        
        Analizi Türkçe olarak, somut ve eyleme dönük önerilerle sun.
        """
        
        return await self._call_gemini(prompt)
    
    def _analyze_seasonality(self, data: pd.DataFrame, product_name: str) -> Dict[str, Any]:
        """Mevsimsel trend analizi"""
        if product_name not in data.columns:
            return {}
        
        try:
            monthly_avg = data[product_name].groupby(data.index.month).mean()
            peak_month = monthly_avg.idxmax()
            low_month = monthly_avg.idxmin()
            
            return {
                "peak_month": int(peak_month),
                "low_month": int(low_month),
                "seasonality_strength": float(monthly_avg.std() / monthly_avg.mean()) if monthly_avg.mean() > 0 else 0
            }
        except Exception:
            return {}
    
    def _calculate_growth_potential(self, trend_data: Dict, competition_data: Dict) -> str:
        """Büyüme potansiyeli hesapla"""
        trend_score = trend_data.get("trend_score")
        competition_score = competition_data.get("competition_score")
        
        # Yüksek trend, düşük rekabet = yüksek potansiyel
        potential_score = trend_score * (1 - competition_score)
        
        if potential_score > 0.6:
            return "Yüksek"
        elif potential_score > 0.3:
            return "Orta"
        else:
            return "Düşük"
    
    def _suggest_entry_timing(self, trend_data: Dict) -> str:
        """Pazara giriş zamanlaması öner"""
        seasonal_data = trend_data.get("seasonal_data", {})
        current_month = datetime.now().month
        
        if seasonal_data and "peak_month" in seasonal_data:
            peak_month = seasonal_data["peak_month"]
            if abs(current_month - peak_month) <= 2:
                return "Şimdi ideal zamanlama"
            else:
                return f"En ideal zaman {peak_month}. ay"
        
        return "Herhangi bir zaman uygun"
    
    def _get_fallback_market_data(self, product: Product) -> Dict[str, Any]:
        """Hata durumunda varsayılan veriler"""
        return {
            "market_size": "YOK",
            "trend_score": 0,
            "competition_level": "YOK",
            "demand_score": 0,
            "seasonal_trends": {},
            "market_insights": f"{product.name} için pazar analizi yapılırken teknik bir sorun oluştu. Genel olarak {product.category} kategorisinde orta seviyede bir pazar potansiyeli görünmektedir.",
            "growth_potential": "YOK",
            "entry_timing": "YOK",
            "analysis_timestamp": datetime.now().isoformat()
        }


class CustomerSegmenter(AIServiceBase):
    """Hedef kitle analizi ve segmentasyon modülü"""
    
    async def analyze_target_audience(self, product: Product, market_data: Dict) -> Dict[str, Any]:
        """Hedef kitle analizi"""
        try:
            # Gemini ile hedef kitle analizi
            audience_analysis = await self._generate_audience_insights(product, market_data)
            
            # Demografik segmentasyon
            demographics = await self._analyze_demographics(product)
            
            # Kanal önerileri
            channels = await self._suggest_marketing_channels(product, demographics)
            
            return {
                "primary_segment": demographics.get("primary_segment", "25-40 yaş arası profesyoneller"),
                "secondary_segments": demographics.get("secondary_segments", []),
                "demographics": demographics,
                "psychographics": await self._analyze_psychographics(product),
                "marketing_channels": channels,
                "content_preferences": await self._analyze_content_preferences(product),
                "audience_insights": audience_analysis,
                "engagement_strategies": await self._suggest_engagement_strategies(product),
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Hedef kitle analizi hatası: {e}")
            return self._get_fallback_audience_data(product)
    
    async def _generate_audience_insights(self, product: Product, market_data: Dict) -> str:
        """Gemini ile hedef kitle içgörüleri"""
        prompt = f"""
        Ürün: {product.name}
        Kategori: {product.category}
        Açıklama: {product.description}
        Fiyat Aralığı: {product.cost_price} TL (maliyet)
        
        Pazar Büyüklüğü: {market_data.get('market_size', 'Orta')}
        Rekabet Seviyesi: {market_data.get('competition_level', 'Orta')}
        
        Bu ürün için Türkiye'de detaylı hedef kitle analizi yap:
        1. Ana hedef kitle demografik profili (yaş, cinsiyet, gelir, eğitim)
        2. Satın alma motivasyonları ve ihtiyaçları
        3. Dijital davranış kalıpları (hangi platformları kullanıyor)
        4. Fiyat hassasiyeti ve satın alma gücü
        5. İletişim tercih ettikleri dil ve ton
        
        Analizi Türkçe, somut ve pazarlama stratejisine yönelik sun.
        """
        
        return await self._call_gemini(prompt)
    
    async def _analyze_demographics(self, product: Product) -> Dict[str, Any]:
        """Demografik analiz"""
        # Ürün kategorisine göre demografik tahminler
        category_demographics = {
            "elektronik": {
                "primary_segment": "18-35 yaş arası teknoloji meraklıları",
                "age_groups": ["18-25", "26-35", "36-45"],
                "gender_distribution": {"erkek": 0.6, "kadın": 0.4},
                "income_level": "orta-üst"
            },
            "giyim": {
                "primary_segment": "20-40 yaş arası moda takipçileri",
                "age_groups": ["20-30", "31-40", "41-50"],
                "gender_distribution": {"erkek": 0.3, "kadın": 0.7},
                "income_level": "orta"
            },
            "ev": {
                "primary_segment": "25-45 yaş arası ev sahipleri",
                "age_groups": ["25-35", "36-45", "46-55"],
                "gender_distribution": {"erkek": 0.4, "kadın": 0.6},
                "income_level": "orta"
            }
        }
        
        # Kategori eşleştirme
        category_key = next((key for key in category_demographics.keys() 
                           if key.lower() in product.category.lower()), "genel")
        
        if category_key == "genel":
            return {
                "primary_segment": "25-40 yaş arası tüketiciler",
                "age_groups": ["25-35", "36-45"],
                "gender_distribution": {"erkek": 0.5, "kadın": 0.5},
                "income_level": "orta"
            }
        
        return category_demographics[category_key]
    
    async def _suggest_marketing_channels(self, product: Product, demographics: Dict) -> List[Dict[str, Any]]:
        """Pazarlama kanalı önerileri"""
        channels = []
        
        # Yaş grubuna göre kanal önerileri
        primary_age = demographics.get("age_groups", ["25-35"])[0]
        age_start = int(primary_age.split("-")[0])
        
        if age_start <= 25:
            channels.extend([
                {"platform": "Instagram", "priority": "yüksek", "content_type": "stories, reels"},
                {"platform": "TikTok", "priority": "yüksek", "content_type": "short videos"},
                {"platform": "YouTube", "priority": "orta", "content_type": "product reviews"}
            ])
        elif age_start <= 35:
            channels.extend([
                {"platform": "Instagram", "priority": "yüksek", "content_type": "posts, stories"},
                {"platform": "Facebook", "priority": "orta", "content_type": "ads, groups"},
                {"platform": "Google Ads", "priority": "yüksek", "content_type": "search ads"}
            ])
        else:
            channels.extend([
                {"platform": "Facebook", "priority": "yüksek", "content_type": "ads, posts"},
                {"platform": "Google Ads", "priority": "yüksek", "content_type": "search ads"},
                {"platform": "E-posta", "priority": "orta", "content_type": "newsletters"}
            ])
        
        return channels
    
    async def _analyze_psychographics(self, product: Product) -> Dict[str, Any]:
        """Psikografik analiz"""
        return {
            "lifestyle": ["teknoloji odaklı", "sosyal medya aktif", "online alışveriş"],
            "values": ["kalite", "güvenilirlik", "uygun fiyat"],
            "interests": [product.category, "yenilikler", "trendler"],
            "buying_behavior": "araştırma yapan, karşılaştırmalı"
        }
    
    async def _analyze_content_preferences(self, product: Product) -> Dict[str, Any]:
        """İçerik tercihleri analizi"""
        return {
            "content_types": ["video", "görsel", "blog yazısı"],
            "tone": "samimi ve bilgilendirici",
            "topics": [f"{product.name} kullanımı", "ipuçları", "karşılaştırmalar"],
            "formats": ["nasıl yapılır", "ürün incelemesi", "müşteri yorumları"]
        }
    
    async def _suggest_engagement_strategies(self, product: Product) -> List[str]:
        """Etkileşim stratejileri"""
        return [
            "Influencer işbirlikleri",
            "Kullanıcı yorumları ve referanslar",
            "Sosyal medya yarışmaları",
            "Ürün deneme kampanyaları",
            "Müşteri hikayelerini paylaşma"
        ]
    
    def _get_fallback_audience_data(self, product: Product) -> Dict[str, Any]:
        """Varsayılan hedef kitle verisi"""
        return {
            "primary_segment": "25-40 yaş arası tüketiciler",
            "secondary_segments": ["18-25 yaş", "41-50 yaş"],
            "demographics": {
                "age_groups": ["25-35", "36-45"],
                "gender_distribution": {"erkek": 0.5, "kadın": 0.5}
            },
            "marketing_channels": [
                {"platform": "Instagram", "priority": "yüksek"},
                {"platform": "Google Ads", "priority": "yüksek"}
            ],
            "audience_insights": f"{product.name} için hedef kitle analiz edilirken teknik sorun oluştu.",
            "analysis_timestamp": datetime.now().isoformat()
        }


class PricingAdvisor(AIServiceBase):
    """Fiyatlandırma ve promosyon stratejisi modülü"""
    
    def __init__(self):
        super().__init__()
        # Exchange Rate servisini başlat
        from app.services.exchange_service import ExchangeRateService
        self.exchange_service = ExchangeRateService()
    
    async def analyze_pricing(self, product: Product, market_data: Dict, audience_data: Dict) -> Dict[str, Any]:
        """Fiyatlandırma analizi"""
        try:
            # Temel fiyat hesaplamaları
            base_pricing = await self._calculate_base_pricing(product)
            
            # Rekabetçi fiyatlandırma
            competitive_pricing = await self._analyze_competitive_pricing(product, market_data)
            
            # Döviz kuru etkisi (Exchange Rate API ile)
            currency_impact = await self._analyze_currency_impact()
            
            # Gemini ile fiyat stratejisi
            pricing_strategy = await self._generate_pricing_strategy(product, base_pricing, competitive_pricing, market_data)
            
            # Promosyon önerileri
            promotion_strategy = await self._suggest_promotions(product, base_pricing, audience_data)
            
            return {
                "recommended_price": base_pricing.get("recommended_price"),
                "price_range": base_pricing.get("price_range"),
                "profit_margin": base_pricing.get("profit_margin"),
                "competitive_position": competitive_pricing.get("position"),
                "pricing_strategy": pricing_strategy,
                "promotion_recommendations": promotion_strategy,
                "price_elasticity": await self._estimate_price_elasticity(product, market_data),
                "seasonal_pricing": await self._suggest_seasonal_pricing(product, market_data),
                "currency_recommendations": currency_impact,
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Fiyatlandırma analizi hatası: {e}")
            return self._get_fallback_pricing_data(product)
    
    async def _calculate_base_pricing(self, product: Product) -> Dict[str, Any]:
        """Temel fiyat hesaplamaları"""
        cost_price = float(product.cost_price)
        
        # Hedef kar marjı (eğer belirtilmişse kullan, yoksa %40 varsayılan)
        target_margin = float(product.target_profit_margin) if product.target_profit_margin else 0.4
        
        # Önerilen fiyat hesaplama
        recommended_price = cost_price * (1 + target_margin)
        
        # Fiyat aralığı
        min_price = cost_price * 1.2  # Minimum %20 kar
        max_price = cost_price * 1.8  # Maksimum %80 kar
        
        return {
            "recommended_price": round(recommended_price, 2),
            "price_range": {
                "min": round(min_price, 2),
                "max": round(max_price, 2)
            },
            "profit_margin": target_margin,
            "cost_price": cost_price
        }
    
    async def _analyze_competitive_pricing(self, product: Product, market_data: Dict) -> Dict[str, Any]:
        """Rekabetçi fiyat analizi"""
        # Market data'dan rakip fiyat bilgilerini al
        competition_level = market_data.get("competition_level", "Orta")
        competitor_analysis = market_data.get("competitor_analysis", {})
        
        # Rakip fiyat verilerini kullan
        price_range = competitor_analysis.get("price_range", {})
        
        if price_range and "avg_price" in price_range:
            avg_competitor_price = price_range["avg_price"]
            min_competitor_price = price_range.get("min_price", avg_competitor_price * 0.8)
            max_competitor_price = price_range.get("max_price", avg_competitor_price * 1.2)
            
            # Rekabet seviyesine göre fiyat pozisyonlama
            if competition_level == "Yüksek":
                position = "aggressive"  # Agresif fiyatlandırma
                target_price = min_competitor_price * 0.95  # Rakiplerden %5 düşük
            elif competition_level == "Düşük":
                position = "premium"  # Premium fiyatlandırma
                target_price = max_competitor_price * 1.1  # Rakiplerden %10 yüksek
            else:
                position = "competitive"  # Rekabetçi fiyatlandırma
                target_price = avg_competitor_price  # Ortalama fiyat
            
            return {
                "position": position,
                "target_price": round(target_price, 2),
                "competitor_avg": round(avg_competitor_price, 2),
                "competitor_range": {
                    "min": round(min_competitor_price, 2),
                    "max": round(max_competitor_price, 2)
                },
                "strategy": f"{competition_level} rekabet ortamında {position} fiyatlandırma önerisi",
                "data_source": competitor_analysis.get("data_source", "Unknown")
            }
        else:
            # Fallback: Rekabet seviyesine göre çarpan
            if competition_level == "Yüksek":
                position = "aggressive"
                multiplier = 0.9
            elif competition_level == "Düşük":
                position = "premium"
                multiplier = 1.2
            else:
                position = "competitive"
                multiplier = 1.0
            
            return {
                "position": position,
                "multiplier": multiplier,
                "strategy": f"{competition_level} rekabet ortamında {position} fiyatlandırma önerisi",
                "note": "Rakip fiyat verisi bulunamadı, genel strateji uygulandı"
            }
    
    async def _analyze_currency_impact(self) -> Dict[str, Any]:
        """Döviz kuru etkisi analizi (Exchange Rate API ile)"""
        try:
            print("💱 Exchange Rate API ile döviz kuru analizi başlatılıyor")
            
            # Exchange Rate API'den güncel kurları al
            rates_data = await self.exchange_service.get_latest_rates("USD")
            
            if rates_data["result"] == "success":
                usd_to_try = rates_data["conversion_rates"].get("TRY", 30.0)
                eur_to_try = rates_data["conversion_rates"].get("EUR", 33.0)
                
                print(f"✅ Güncel kurlar alındı: USD/TRY={usd_to_try}, EUR/TRY={eur_to_try}")
                
                # Kur etkisi analizi
                if usd_to_try > 32:
                    impact = "yüksek"
                    recommendation = "TL bazlı fiyatlandırma ve sık güncelleme önerilir"
                elif usd_to_try < 28:
                    impact = "düşük"
                    recommendation = "Mevcut fiyatlandırma stratejinizi koruyabilirsiniz"
                else:
                    impact = "orta"
                    recommendation = "Döviz kurundaki değişiklikleri takip edin"
                
                # Para birimi önerileri
                currency_suggestions = []
                if usd_to_try > 30:
                    currency_suggestions.append("TL fiyatlarını haftalık güncelleyin")
                if eur_to_try > 32:
                    currency_suggestions.append("EUR bazlı fiyatlandırma düşünün")
                
                return {
                    "usd_to_try": usd_to_try,
                    "eur_to_try": eur_to_try,
                    "impact": impact,
                    "recommendation": recommendation,
                    "currency_suggestions": currency_suggestions,
                    "last_update": rates_data.get("time_last_update_utc"),
                    "data_source": "Exchange Rate API"
                }
            else:
                print("⚠️ Exchange Rate API başarısız, fallback kullanılıyor")
                return self._get_fallback_currency_data()
                
        except Exception as e:
            print(f"❌ Döviz kuru analizi hatası: {e}")
            return self._get_fallback_currency_data()
    
    def _get_fallback_currency_data(self) -> Dict[str, Any]:
        """Fallback döviz kuru verisi"""
        return {
            "usd_to_try": 30.0,
            "eur_to_try": 33.0,
            "impact": "bilinmiyor",
            "recommendation": "Döviz kuru verisi alınamadı, manuel takip önerilir",
            "currency_suggestions": ["Döviz kurlarını manuel olarak takip edin"],
            "data_source": "Fallback",
            "note": "API bağlantısı kurulamadı, varsayılan veriler kullanılıyor"
        }
    
    async def _generate_pricing_strategy(self, product: Product, base_pricing: Dict, competitive_pricing: Dict, market_data: Dict) -> str:
        """Gemini ile fiyat stratejisi oluştur"""
        prompt = f"""
        Ürün: {product.name}
        Kategori: {product.category}
        Maliyet Fiyatı: {product.cost_price} TL
        Önerilen Fiyat: {base_pricing.get('recommended_price')} TL
        Kar Marjı: %{base_pricing.get('profit_margin', 0.4) * 100}
        
        Pazar Durumu:
        - Pazar Büyüklüğü: {market_data.get('market_size', 'Orta')}
        - Rekabet Seviyesi: {market_data.get('competition_level', 'Orta')}
        - Talep Skoru: {market_data.get('demand_score', 0.6)}
        
        Rekabet Pozisyonu: {competitive_pricing.get('position', 'competitive')}
        
        Bu ürün için kapsamlı fiyatlandırma stratejisi geliştir:
        1. Fiyat pozisyonlama stratejisi
        2. Pazar giriş fiyatı önerisi
        3. Fiyat artış/azalış senaryoları
        4. Rakiplere karşı avantajlar
        5. Müşteri değer algısını artırma yöntemleri
        
        Stratejiyi Türkçe, uygulanabilir ve somut önerilerle sun.
        """
        
        return await self._call_gemini(prompt)
    
    async def _suggest_promotions(self, product: Product, base_pricing: Dict, audience_data: Dict) -> List[Dict[str, Any]]:
        """Promosyon önerileri"""
        recommended_price = base_pricing.get("recommended_price", 100)
        
        promotions = [
            {
                "type": "İlk Müşteri İndirimi",
                "discount": "15%",
                "target_price": round(recommended_price * 0.85, 2),
                "duration": "İlk 30 gün",
                "target_audience": "Yeni müşteriler"
            },
            {
                "type": "Toplu Alım İndirimi",
                "discount": "2+1",
                "target_price": recommended_price,
                "duration": "Sürekli",
                "target_audience": "Toplu alım yapanlar"
            },
            {
                "type": "Mevsimsel Kampanya",
                "discount": "20%",
                "target_price": round(recommended_price * 0.8, 2),
                "duration": "Sezon sonu",
                "target_audience": "Tüm müşteriler"
            }
        ]
        
        return promotions
    
    async def _estimate_price_elasticity(self, product: Product, market_data: Dict) -> Dict[str, Any]:
        """Fiyat elastikiyeti tahmini"""
        competition_level = market_data.get("competition_level", "Orta")
        
        if competition_level == "Yüksek":
            elasticity = "yüksek"
            sensitivity = 0.8
        elif competition_level == "Düşük":
            elasticity = "düşük"
            sensitivity = 0.3
        else:
            elasticity = "orta"
            sensitivity = 0.5
        
        return {
            "elasticity_level": elasticity,
            "price_sensitivity": sensitivity,
            "recommendation": f"Fiyat değişikliklerinde {elasticity} hassasiyet beklenir"
        }
    
    async def _suggest_seasonal_pricing(self, product: Product, market_data: Dict) -> Dict[str, Any]:
        """Mevsimsel fiyatlandırma önerileri"""
        seasonal_trends = market_data.get("seasonal_trends", {})
        
        if seasonal_trends and "peak_month" in seasonal_trends:
            peak_month = seasonal_trends["peak_month"]
            return {
                "peak_season": f"{peak_month}. ay",
                "peak_price_increase": "10-15%",
                "off_season_discount": "10-20%",
                "strategy": "Yoğun dönemlerde fiyat artışı, durgun dönemlerde indirim"
            }
        
        return {
            "strategy": "Mevsimsel fiyat değişikliği önerilmez",
            "recommendation": "Sabit fiyat stratejisi uygulayın"
        }
    
    def _get_fallback_pricing_data(self, product: Product) -> Dict[str, Any]:
        """Varsayılan fiyatlandırma verisi"""
        cost_price = float(product.cost_price)
        recommended_price = cost_price * 1.4
        
        return {
            "recommended_price": round(recommended_price, 2),
            "price_range": {
                "min": round(cost_price * 1.2, 2),
                "max": round(cost_price * 1.8, 2)
            },
            "profit_margin": 0.4,
            "pricing_strategy": f"{product.name} için fiyat analizi yapılırken teknik sorun oluştu. Genel olarak %40 kar marjı önerilir.",
            "analysis_timestamp": datetime.now().isoformat()
        }


class MessagingGenerator(AIServiceBase):
    """İçerik ve mesajlaşma stratejisi modülü"""
    
    async def generate_messaging_strategy(self, product: Product, market_data: Dict, audience_data: Dict, pricing_data: Dict) -> Dict[str, Any]:
        """Mesajlaşma stratejisi oluştur"""
        try:
            # SEO optimized içerik
            seo_content = await self._generate_seo_content(product, market_data)
            
            # Pazarlama mesajları
            marketing_messages = await self._generate_marketing_messages(product, audience_data, pricing_data)
            
            # Sosyal medya içeriği
            social_content = await self._generate_social_media_content(product, audience_data)
            
            # E-posta kampanya içeriği
            email_content = await self._generate_email_content(product, pricing_data)
            
            return {
                "seo_content": seo_content,
                "marketing_messages": marketing_messages,
                "social_media_content": social_content,
                "email_campaigns": email_content,
                "key_messages": await self._extract_key_messages(product, audience_data),
                "tone_of_voice": await self._define_tone_of_voice(product, audience_data),
                "content_calendar": await self._suggest_content_calendar(product),
                "ab_test_recommendations": await self._suggest_ab_tests(product),
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Mesajlaşma stratejisi hatası: {e}")
            return self._get_fallback_messaging_data(product)
    
    async def _generate_seo_content(self, product: Product, market_data: Dict) -> Dict[str, Any]:
        """SEO optimized içerik oluştur"""
        prompt = f"""
        Ürün: {product.name}
        Kategori: {product.category}
        Açıklama: {product.description}
        
        Bu ürün için SEO optimized içerik oluştur:
        1. Ana başlık (H1) - 60 karakter altında
        2. Meta açıklama - 160 karakter altında
        3. 5 anahtar kelime önerisi
        4. Ürün açıklaması - 200 kelime, anahtar kelime yoğunluğu %2-3
        5. Alt başlıklar (H2, H3) önerileri
        
        İçeriği Türkçe, doğal ve kullanıcı dostu şekilde yaz.
        """
        
        seo_response = await self._call_gemini(prompt)
        
        return {
            "optimized_title": f"{product.name} - Kaliteli {product.category}",
            "meta_description": f"{product.name} satın al. {product.category} kategorisinde en iyi fiyatlar ve kalite garantisi.",
            "keywords": [product.name.lower(), product.category.lower(), "satın al", "fiyat", "kaliteli"],
            "optimized_description": seo_response,
            "headings": [
                f"{product.name} Özellikleri",
                f"Neden {product.name} Seçmeli?",
                f"{product.category} Kategorisinde En İyi"
            ]
        }
    
    async def _generate_marketing_messages(self, product: Product, audience_data: Dict, pricing_data: Dict) -> Dict[str, Any]:
        """Pazarlama mesajları oluştur"""
        primary_segment = audience_data.get("primary_segment", "hedef kitle")
        recommended_price = pricing_data.get("recommended_price", 100)
        
        prompt = f"""
        Ürün: {product.name}
        Hedef Kitle: {primary_segment}
        Fiyat: {recommended_price} TL
        
        Bu ürün ve hedef kitle için pazarlama mesajları oluştur:
        1. Ana değer önerisi (value proposition) - 1 cümle
        2. 3 adet satış noktası (selling points)
        3. Call-to-action (CTA) önerileri - 5 farklı
        4. Reklamda kullanılacak slogan - 3 alternatif
        5. Müşteri itirazlarına cevaplar - 3 adet
        
        Mesajları Türkçe, ikna edici ve hedef kitleye uygun şekilde yaz.
        """
        
        marketing_response = await self._call_gemini(prompt)
        
        return {
            "value_proposition": f"{product.name} ile {product.category} ihtiyaçlarınızı karşılayın",
            "selling_points": [
                "Yüksek kalite standartları",
                "Uygun fiyat garantisi",
                "Hızlı teslimat"
            ],
            "call_to_actions": [
                "Hemen Satın Al",
                "Sepete Ekle",
                "Fiyat Teklifi Al",
                "Ücretsiz Deneme",
                "Detaylı Bilgi Al"
            ],
            "slogans": [
                f"{product.name} - Kaliteden Ödün Verme",
                f"En İyi {product.category} Burada",
                f"{product.name} ile Farkı Yaşa"
            ],
            "detailed_messages": marketing_response
        }
    
    async def _generate_social_media_content(self, product: Product, audience_data: Dict) -> Dict[str, Any]:
        """Sosyal medya içeriği oluştur"""
        channels = audience_data.get("marketing_channels", [])
        
        content = {}
        
        for channel in channels:
            platform = channel.get("platform", "Instagram")
            
            if platform == "Instagram":
                content["instagram"] = {
                    "post_ideas": [
                        f"{product.name} kullanım ipuçları",
                        "Müşteri yorumları ve fotoğrafları",
                        "Ürün detay görselleri",
                        "Behind the scenes içerik"
                    ],
                    "hashtags": [f"#{product.name.replace(' ', '')}", f"#{product.category}", "#kalite", "#türkiye"],
                    "story_ideas": ["Günün ürünü", "Müşteri deneyimleri", "Hızlı ipuçları"]
                }
            elif platform == "Facebook":
                content["facebook"] = {
                    "post_types": ["Bilgilendirici yazılar", "Müşteri hikayeleri", "Ürün tanıtımları"],
                    "ad_formats": ["Carousel ads", "Video ads", "Collection ads"]
                }
        
        return content
    
    async def _generate_email_content(self, product: Product, pricing_data: Dict) -> Dict[str, Any]:
        """E-posta kampanya içeriği"""
        return {
            "welcome_series": {
                "subject": f"{product.name} ile tanışın!",
                "content": f"Merhaba! {product.name} ürünümüzü tercih ettiğiniz için teşekkürler."
            },
            "promotional": {
                "subject": f"{product.name} için özel indirim!",
                "content": f"Sadece sizin için {product.name} ürününde %15 indirim fırsatı."
            },
            "educational": {
                "subject": f"{product.name} nasıl kullanılır?",
                "content": f"{product.name} ürününüzden en iyi şekilde yararlanmanız için ipuçları."
            }
        }
    
    async def _extract_key_messages(self, product: Product, audience_data: Dict) -> List[str]:
        """Anahtar mesajları çıkar"""
        return [
            "Kalite ve güvenilirlik",
            "Uygun fiyat avantajı",
            "Müşteri memnuniyeti odaklı",
            "Hızlı ve güvenli teslimat"
        ]
    
    async def _define_tone_of_voice(self, product: Product, audience_data: Dict) -> Dict[str, str]:
        """Ses tonu tanımla"""
        primary_segment = audience_data.get("primary_segment", "")
        
        if "genç" in primary_segment.lower() or "18-25" in primary_segment:
            return {
                "tone": "Samimi ve enerjik",
                "style": "Günlük dil, emoji kullanımı",
                "personality": "Arkadaş canlısı, trend takipçisi"
            }
        else:
            return {
                "tone": "Profesyonel ve güvenilir",
                "style": "Resmi ama sıcak dil",
                "personality": "Uzman, güvenilir, çözüm odaklı"
            }
    
    async def _suggest_content_calendar(self, product: Product) -> Dict[str, List[str]]:
        """İçerik takvimi öner"""
        return {
            "haftalık": [
                "Pazartesi: Ürün tanıtımı",
                "Çarşamba: Müşteri yorumu",
                "Cuma: İpucu ve trick",
                "Pazar: Behind the scenes"
            ],
            "aylık": [
                "Ayın ilk haftası: Yeni ürün lansmanı",
                "İkinci hafta: Eğitici içerik",
                "Üçüncü hafta: Müşteri hikayeleri",
                "Dördüncü hafta: Promosyon kampanyası"
            ]
        }
    
    async def _suggest_ab_tests(self, product: Product) -> List[Dict[str, str]]:
        """A/B test önerileri"""
        return [
            {
                "test_type": "Başlık testi",
                "variant_a": f"{product.name} - En İyi Seçim",
                "variant_b": f"Kaliteli {product.name} Burada",
                "metric": "Tıklama oranı"
            },
            {
                "test_type": "CTA testi",
                "variant_a": "Hemen Satın Al",
                "variant_b": "Sepete Ekle",
                "metric": "Dönüşüm oranı"
            },
            {
                "test_type": "Görsel testi",
                "variant_a": "Ürün tek başına",
                "variant_b": "Ürün kullanım halinde",
                "metric": "Engagement oranı"
            }
        ]
    
    def _get_fallback_messaging_data(self, product: Product) -> Dict[str, Any]:
        """Varsayılan mesajlaşma verisi"""
        return {
            "key_messages": ["Kalite", "Güvenilirlik", "Uygun fiyat"],
            "tone_of_voice": {
                "tone": "Profesyonel ve samimi",
                "style": "Anlaşılır dil"
            },
            "marketing_messages": {
                "value_proposition": f"{product.name} ile ihtiyaçlarınızı karşılayın"
            },
            "analysis_timestamp": datetime.now().isoformat()
        }


class StrategyBuilder(AIServiceBase):
    """Merkezi strateji oluşturma motoru"""
    
    def __init__(self):
        super().__init__()
        self.market_analyzer = MarketAnalyzer()
        self.customer_segmenter = CustomerSegmenter()
        self.pricing_advisor = PricingAdvisor()
        self.messaging_generator = MessagingGenerator()
        self.rag_engine = RAGEmbeddingEngine()
    
    async def build_comprehensive_strategy(self, product: Product) -> Dict[str, Any]:
        """Kapsamlı satış stratejisi oluştur"""
        try:
            print(f"🔄 {product.name} için AI analizi başlatılıyor...")
            
            # 0. PDF Kütüphanesinden ilgili stratejileri al
            print("📚 PDF kütüphanesinden ilgili stratejiler aranıyor...")
            pdf_context = await self.rag_engine.get_pdf_context_for_strategy(
                product.category, 
                product.name
            )
            if pdf_context:
                print(f"✅ {len(pdf_context.split('Kaynak'))} PDF kaynağından bilgi alındı")
            else:
                print("ℹ️ PDF kütüphanesinde ilgili strateji bulunamadı")
            
            # 1. Pazar analizi
            print("📊 Pazar analizi yapılıyor...")
            market_data = await self.market_analyzer.analyze_market(product)
            
            # 2. Hedef kitle analizi
            print("🎯 Hedef kitle analizi yapılıyor...")
            audience_data = await self.customer_segmenter.analyze_target_audience(product, market_data)
            
            # 3. Fiyatlandırma analizi
            print("💰 Fiyatlandırma analizi yapılıyor...")
            pricing_data = await self.pricing_advisor.analyze_pricing(product, market_data, audience_data)
            
            # 4. Mesajlaşma stratejisi
            print("✍️ Mesajlaşma stratejisi oluşturuluyor...")
            messaging_data = await self.messaging_generator.generate_messaging_strategy(
                product, market_data, audience_data, pricing_data
            )
            
            # 5. Nihai strateji oluşturma
            print("🧠 Nihai strateji oluşturuluyor...")
            final_strategy = await self._generate_final_strategy(
                product, market_data, audience_data, pricing_data, messaging_data, pdf_context
            )
            
            print("✅ AI analizi tamamlandı!")
            
            return {
                "strategy_content": final_strategy,
                "market_analysis": market_data,
                "audience_analysis": audience_data,
                "pricing_analysis": pricing_data,
                "messaging_analysis": messaging_data,
                "confidence_score": self._calculate_confidence_score(market_data, audience_data, pricing_data),
                "expected_roi": self._estimate_roi(pricing_data, market_data),
                "implementation_difficulty": self._assess_difficulty(market_data, audience_data),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Strateji oluşturma hatası: {e}")
            raise e

    async def analyze_market_only(self, product):
        """Sadece pazar analizi yap"""
        try:
            print(f"📊 Pazar analizi başlatılıyor: {product.name}")
            market_data = await self.market_analyzer.analyze_market(product)
            print(f"✅ Pazar analizi tamamlandı: {product.name}")
            return market_data
        except Exception as e:
            print(f"❌ Pazar analizi hatası: {e}")
            raise e

    async def analyze_customer_only(self, product):
        """Sadece hedef kitle analizi yap"""
        try:
            print(f"🎯 Hedef kitle analizi başlatılıyor: {product.name}")
            # Basit pazar verisi oluştur (tam analiz için gerekli)
            basic_market_data = {"market_size": "Orta", "competition_level": "Orta", "demand_score": 0.7}
            audience_data = await self.customer_segmenter.analyze_target_audience(product, basic_market_data)
            print(f"✅ Hedef kitle analizi tamamlandı: {product.name}")
            return audience_data
        except Exception as e:
            print(f"❌ Hedef kitle analizi hatası: {e}")
            raise e

    async def analyze_pricing_only(self, product):
        """Sadece fiyatlandırma analizi yap"""
        try:
            print(f"💰 Fiyatlandırma analizi başlatılıyor: {product.name}")
            # Basit veriler oluştur
            basic_market_data = {"market_size": "Orta", "competition_level": "Orta", "demand_score": 0.7}
            basic_audience_data = {"primary_segment": "Genel Tüketici", "price_sensitivity": "Orta"}
            pricing_data = await self.pricing_advisor.analyze_pricing(product, basic_market_data, basic_audience_data)
            print(f"✅ Fiyatlandırma analizi tamamlandı: {product.name}")
            return pricing_data
        except Exception as e:
            print(f"❌ Fiyatlandırma analizi hatası: {e}")
            raise e

    async def analyze_messaging_only(self, product):
        """Sadece mesajlaşma stratejisi analizi yap"""
        try:
            print(f"✍️ Mesajlaşma analizi başlatılıyor: {product.name}")
            # Basit veriler oluştur
            basic_market_data = {"market_size": "Orta", "competition_level": "Orta", "demand_score": 0.7}
            basic_audience_data = {"primary_segment": "Genel Tüketici", "interests": ["Teknoloji"]}
            basic_pricing_data = {"recommended_price": product.cost_price * 1.4}
            messaging_data = await self.messaging_generator.generate_messaging_strategy(
                product, basic_market_data, basic_audience_data, basic_pricing_data
            )
            print(f"✅ Mesajlaşma analizi tamamlandı: {product.name}")
            return messaging_data
        except Exception as e:
            print(f"❌ Mesajlaşma analizi hatası: {e}")
            raise e

    async def generate_final_strategy(self, product, combined_data):
        """Analiz sonuçlarından nihai stratejiyi oluştur"""
        try:
            print(f"🚀 Nihai strateji oluşturuluyor: {product.name}")
            
            # PDF context al
            pdf_context = ""
            if hasattr(self, 'rag_engine') and self.rag_engine:
                pdf_context = await self.rag_engine.get_pdf_context_for_strategy(
                    product.category, 
                    product.name
                )
            
            final_strategy = await self._generate_final_strategy(
                product, 
                combined_data.get("market_analysis", {}),
                combined_data.get("customer_analysis", {}),
                combined_data.get("pricing_analysis", {}),
                combined_data.get("messaging_analysis", {}),
                pdf_context
            )
            
            print(f"✅ Nihai strateji oluşturuldu: {product.name}")
            
            return {
                "strategy_content": final_strategy,
                "confidence_score": self._calculate_confidence_score(
                    combined_data.get("market_analysis", {}),
                    combined_data.get("customer_analysis", {}),
                    combined_data.get("pricing_analysis", {})
                ),
                "expected_roi": self._estimate_roi(
                    combined_data.get("pricing_analysis", {}),
                    combined_data.get("market_analysis", {})
                ),
                "implementation_difficulty": self._assess_difficulty(
                    combined_data.get("market_analysis", {}),
                    combined_data.get("customer_analysis", {})
                ),
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Nihai strateji oluşturma hatası: {e}")
            raise e
    
    async def _generate_final_strategy(self, product: Product, market_data: Dict, audience_data: Dict, 
                                     pricing_data: Dict, messaging_data: Dict, pdf_context: str = "") -> str:
        """Gemini ile nihai strateji metni oluştur"""
        
        prompt = f"""
        ÜRÜN BİLGİLERİ:
        - Ürün Adı: {product.name}
        - Kategori: {product.category}
        - Açıklama: {product.description}
        - Maliyet Fiyatı: {product.cost_price} TL
        
        PAZAR ANALİZİ:
        - Pazar Büyüklüğü: {market_data.get('market_size', 'Orta')}
        - Rekabet Seviyesi: {market_data.get('competition_level', 'Orta')}
        - Talep Skoru: {market_data.get('demand_score', 0.6)}
        - Büyüme Potansiyeli: {market_data.get('growth_potential', 'Orta')}
        
        HEDEF KİTLE:
        - Ana Segment: {audience_data.get('primary_segment', 'Genel tüketiciler')}
        - Pazarlama Kanalları: {', '.join([ch.get('platform', '') for ch in audience_data.get('marketing_channels', [])])}
        
        FİYATLANDIRMA:
        - Önerilen Fiyat: {pricing_data.get('recommended_price', 100)} TL
        - Kar Marjı: %{(pricing_data.get('profit_margin', 0.4) * 100):.0f}
        - Rekabet Pozisyonu: {pricing_data.get('competitive_position', 'competitive')}
        
        MESAJLAŞMA:
        - Ana Mesajlar: {', '.join(messaging_data.get('key_messages', ['Kalite', 'Güvenilirlik']))}
        - Ses Tonu: {messaging_data.get('tone_of_voice', {}).get('tone', 'Profesyonel')}
        
        {'ÖNCEDEN YÜKLENMIŞ STRATEJİ BİLGİLERİ (PDF KÜTÜPHANE):' if pdf_context else ''}
        {pdf_context if pdf_context else ''}
        {'Yukarıdaki kaynaklardan elde ettiğin bilgileri de dikkate alarak,' if pdf_context else ''} Bu verilere dayanarak {product.name} için kapsamlı ve uygulanabilir bir satış stratejisi oluştur. 
        Strateji şu bölümleri içermeli:
        
        1. **Yönetici Özeti** (2-3 cümle)
        2. **Pazar Pozisyonlama Stratejisi**
        3. **Hedef Kitle ve Pazarlama Yaklaşımı**
        4. **Fiyatlandırma ve Rekabet Stratejisi**
        5. **Pazarlama ve İletişim Planı**
        6. **Uygulama Adımları** (öncelik sırasına göre)
        7. **Başarı Metrikleri ve Takip**
        8. **Risk Analizi ve Önlemler**
        9. **İlk 90 Günlük Eylem Planı**
        
        Stratejiyi Türkçe, profesyonel, somut ve hemen uygulanabilir şekilde yaz. 
        Her bölümde spesifik öneriler ve sayısal hedefler ver.
        """
        
        strategy_text = await self._call_gemini(prompt)
        
        # Eğer Gemini yanıt veremezse fallback strateji
        if not strategy_text or "hata" in strategy_text.lower():
            return self._create_fallback_strategy_text(product, market_data, audience_data, pricing_data)
        
        return strategy_text
    
    def _create_fallback_strategy_text(self, product: Product, market_data: Dict, 
                                     audience_data: Dict, pricing_data: Dict) -> str:
        """Fallback strateji metni"""
        recommended_price = pricing_data.get('recommended_price', product.cost_price * 1.4)
        primary_segment = audience_data.get('primary_segment', 'hedef kitle')
        
        return f"""
        # {product.name} Satış Stratejisi
        
        ## 1. Yönetici Özeti
        {product.name} için geliştirilen bu strateji, {market_data.get('market_size', 'orta')} büyüklükteki pazarda 
        {primary_segment} hedef kitleye odaklanarak {recommended_price} TL fiyat noktasında konumlanmayı hedeflemektedir.
        
        ## 2. Pazar Pozisyonlama
        - **Pazar Konumu**: {market_data.get('competition_level', 'Orta')} rekabet ortamında kalite odaklı konumlanma
        - **Değer Önerisi**: Kaliteli {product.category} ürünü, uygun fiyat garantisi ile
        - **Rekabet Avantajı**: Müşteri odaklı yaklaşım ve güvenilir hizmet
        
        ## 3. Hedef Kitle Stratejisi
        - **Ana Hedef**: {primary_segment}
        - **Pazarlama Kanalları**: Online platformlar (Instagram, Google Ads, Facebook)
        - **Mesajlaşma**: Kalite, güvenilirlik ve uygun fiyat vurgusu
        
        ## 4. Fiyatlandırma Stratejisi
        - **Ana Fiyat**: {recommended_price} TL
        - **Kar Marjı**: %{(pricing_data.get('profit_margin', 0.4) * 100):.0f}
        - **Promosyon**: İlk müşterilere %15 indirim
        
        ## 5. Pazarlama Planı
        - **Dijital Pazarlama**: Sosyal medya reklamları ve Google Ads
        - **İçerik Stratejisi**: Ürün tanıtım videoları ve müşteri yorumları
        - **Influencer İşbirliği**: Sektör influencerları ile çalışma
        
        ## 6. Uygulama Adımları
        1. Ürün fiyatını {recommended_price} TL olarak belirle
        2. Sosyal medya hesaplarını optimize et
        3. Google Ads kampanyası başlat
        4. Müşteri geri bildirim sistemi kur
        5. Performans takip sistemini aktive et
        
        ## 7. Başarı Metrikleri
        - **Satış Hedefi**: İlk 3 ayda 100 adet satış
        - **Dönüşüm Oranı**: %2-3 hedefi
        - **Müşteri Memnuniyeti**: %85+ hedefi
        - **ROI**: %{(pricing_data.get('profit_margin', 0.4) * 100):.0f} kar marjı
        
        ## 8. Risk Analizi
        - **Yüksek Rekabet**: Fiyat avantajı ve kalite ile karşıla
        - **Düşük Talep**: Pazarlama bütçesini artır
        - **Maliyet Artışı**: Tedarikçi alternatiflerini değerlendir
        
        ## 9. İlk 90 Günlük Plan
        **1-30 Gün**: Ürün lansmanı ve ilk pazarlama kampanyaları
        **31-60 Gün**: Müşteri geri bildirimlerine göre optimizasyon
        **61-90 Gün**: Performans değerlendirmesi ve strateji güncellemesi
        """
    
    def _calculate_confidence_score(self, market_data: Dict, audience_data: Dict, pricing_data: Dict) -> float:
        """Strateji güven skorunu hesapla"""
        scores = []
        
        # Pazar verisi kalitesi
        if market_data.get('trend_score', 0) > 0:
            scores.append(0.9)
        else:
            scores.append(0.6)
        
        # Hedef kitle verisi
        if audience_data.get('primary_segment'):
            scores.append(0.85)
        else:
            scores.append(0.7)
        
        # Fiyat verisi
        if pricing_data.get('recommended_price'):
            scores.append(0.9)
        else:
            scores.append(0.75)
        
        return round(sum(scores) / len(scores), 2)
    
    def _estimate_roi(self, pricing_data: Dict, market_data: Dict) -> float:
        """ROI tahmini"""
        base_roi = pricing_data.get('profit_margin', 0.4)
        
        # Pazar büyüklüğüne göre ayarlama
        market_size = market_data.get('market_size', 'Orta')
        if market_size == 'Büyük':
            base_roi *= 1.2
        elif market_size == 'Küçük':
            base_roi *= 0.8
        
        # Rekabet seviyesine göre ayarlama
        competition_level = market_data.get('competition_level', 'Orta')
        if competition_level == 'Yüksek':
            base_roi *= 0.8
        elif competition_level == 'Düşük':
            base_roi *= 1.3
        
        return round(min(base_roi, 0.6), 2)  # Maksimum %60 ROI
    
    def _assess_difficulty(self, market_data: Dict, audience_data: Dict) -> str:
        """Uygulama zorluğu değerlendirmesi"""
        difficulty_score = 0
        
        # Rekabet seviyesi
        competition_level = market_data.get('competition_level', 'Orta')
        if competition_level == 'Yüksek':
            difficulty_score += 2
        elif competition_level == 'Orta':
            difficulty_score += 1
        
        # Hedef kitle karmaşıklığı
        channels = len(audience_data.get('marketing_channels', []))
        if channels > 3:
            difficulty_score += 1
        
        if difficulty_score <= 1:
            return 'easy'
        elif difficulty_score <= 2:
            return 'medium'
        else:
            return 'hard'
    
    async def _generate_fallback_strategy(self, product: Product) -> Dict[str, Any]:
        """Hata durumunda basit strateji"""
        recommended_price = float(product.cost_price) * 1.4
        
        fallback_content = f"""
        # {product.name} Basit Satış Stratejisi
        
        ## Genel Bakış
        {product.name} ürününüz için temel satış stratejisi hazırlanmıştır.
        
        ## Fiyatlandırma
        - Önerilen satış fiyatı: {recommended_price:.2f} TL
        - Hedef kar marjı: %40
        
        ## Pazarlama
        - Online satış kanallarına odaklanın
        - Sosyal medya reklamları yapın
        - Müşteri yorumlarını toplayın
        
        ## Uygulama
        1. Fiyatı belirleyin
        2. Online mağaza açın
        3. Pazarlama kampanyası başlatın
        4. Satış sonuçlarını takip edin
        """
        
        return {
            "strategy_content": fallback_content,
            "confidence_score": 0.6,
            "expected_roi": 0.3,
            "implementation_difficulty": "medium",
            "created_at": datetime.now().isoformat()
        } 