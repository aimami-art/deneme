"""
SerpAPI Servisi
Google arama sonuçları ve Google Shopping verilerini almak için kullanılır
"""

import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.core.config import settings


class SerpApiService:
    """SerpAPI ile Google arama ve shopping verileri"""
    
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search"
        self.cache = {}  # Basit in-memory cache
        self.cache_ttl = 86400  # 24 saat
    
    async def search_google_shopping(self, product_name: str, location: str = "Turkey") -> Dict[str, Any]:
        """Google Shopping sonuçları"""
        cache_key = f"shopping_{product_name}_{location}"
        
        # Cache kontrolü
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() < cached_data["expires_at"]:
                return cached_data["data"]
        
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_shopping",
                "q": product_name,
                "location": location,
                "hl": "tr",
                "gl": "tr",
                "google_domain": "google.com.tr"
            }
            
            response = await asyncio.to_thread(requests.get, self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache'e kaydet
                self.cache[cache_key] = {
                    "data": data,
                    "expires_at": datetime.now() + timedelta(seconds=self.cache_ttl)
                }
                
                return data
            else:
                print(f"❌ SerpAPI Shopping hatası: {response.status_code}")
                return self._get_fallback_shopping_results(product_name)
                
        except Exception as e:
            print(f"❌ SerpAPI Shopping bağlantı hatası: {str(e)}")
            return self._get_fallback_shopping_results(product_name)
    
    async def analyze_competitors(self, product_name: str, category: str = None) -> Dict[str, Any]:
        """Rakip analizi yap"""
        try:
            # Arama sorgusu oluştur
            query = product_name
            if category:
                query = f"{product_name} {category}"
            
            # Google Shopping'den verileri al
            shopping_results = await self.search_google_shopping(query)
            
            # Sonuçları analiz et
            shopping_results_data = shopping_results.get("shopping_results", [])
            
            if not shopping_results_data:
                return self._get_fallback_competitor_analysis(product_name)
            
            # Fiyat analizi
            prices = []
            sellers = []
            features = []
            
            for item in shopping_results_data:
                # Fiyat çıkarma
                if "price" in item:
                    price_str = item["price"]
                    # Türkçe fiyat formatını parse et (örn: "1.234,56 TL")
                    price_clean = price_str.replace("TL", "").replace("₺", "").strip()
                    price_clean = price_clean.replace(".", "").replace(",", ".")
                    try:
                        price = float(price_clean)
                        if price > 0:
                            prices.append(price)
                    except (ValueError, TypeError):
                        pass
                
                # Satıcı bilgisi
                if "source" in item:
                    sellers.append(item["source"])
                
                # Ürün özellikleri
                if "snippet" in item:
                    features.append(item["snippet"])
            
            if not prices:
                return self._get_fallback_competitor_analysis(product_name)
            
            # İstatistikler hesapla
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            competitor_count = len(shopping_results_data)
            
            # Rekabet seviyesi belirle
            if competitor_count > 20:
                competition_level = "Yüksek"
            elif competitor_count > 10:
                competition_level = "Orta"
            else:
                competition_level = "Düşük"
            
            return {
                "success": True,
                "product_name": product_name,
                "competitor_count": competitor_count,
                "competition_level": competition_level,
                "price_analysis": {
                    "min_price": round(min_price, 2),
                    "max_price": round(max_price, 2),
                    "avg_price": round(avg_price, 2),
                    "price_range": round(max_price - min_price, 2)
                },
                "top_sellers": list(set(sellers))[:5],  # Benzersiz satıcılar, max 5
                "popular_features": features[:5],  # İlk 5 özellik
                "raw_results": shopping_results_data[:10],  # Ham veriler (ilk 10)
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Rakip analizi hatası: {str(e)}")
            return self._get_fallback_competitor_analysis(product_name)
    
    async def search_google(self, query: str, location: str = "Turkey") -> Dict[str, Any]:
        """Genel Google arama sonuçları"""
        cache_key = f"google_{query}_{location}"
        
        # Cache kontrolü
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() < cached_data["expires_at"]:
                return cached_data["data"]
        
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google",
                "q": query,
                "location": location,
                "hl": "tr",
                "gl": "tr",
                "google_domain": "google.com.tr"
            }
            
            response = await asyncio.to_thread(requests.get, self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache'e kaydet
                self.cache[cache_key] = {
                    "data": data,
                    "expires_at": datetime.now() + timedelta(seconds=self.cache_ttl)
                }
                
                return data
            else:
                print(f"❌ SerpAPI Google hatası: {response.status_code}")
                return self._get_fallback_search_results(query)
                
        except Exception as e:
            print(f"❌ SerpAPI Google bağlantı hatası: {str(e)}")
            return self._get_fallback_search_results(query)
    
    def _get_fallback_shopping_results(self, product_name: str) -> Dict[str, Any]:
        """Fallback Google Shopping sonuçları"""
        return {
            "search_metadata": {
                "status": "Success",
                "created_at": datetime.now().isoformat(),
                "engine_url": f"https://www.google.com.tr/search?q={product_name}&tbm=shop"
            },
            "search_parameters": {
                "engine": "google_shopping",
                "q": product_name,
                "location": "Turkey"
            },
            "shopping_results": [],
            "error": "API bağlantısı kurulamadı - fallback veriler kullanılıyor"
        }
    
    def _get_fallback_search_results(self, query: str) -> Dict[str, Any]:
        """Fallback Google arama sonuçları"""
        return {
            "search_metadata": {
                "status": "Success",
                "created_at": datetime.now().isoformat(),
                "engine_url": f"https://www.google.com.tr/search?q={query}"
            },
            "search_parameters": {
                "engine": "google",
                "q": query,
                "location": "Turkey"
            },
            "organic_results": [],
            "error": "API bağlantısı kurulamadı - fallback veriler kullanılıyor"
        }
    
    def _get_fallback_competitor_analysis(self, product_name: str) -> Dict[str, Any]:
        """Fallback rakip analizi"""
        return {
            "success": False,
            "product_name": product_name,
            "competitor_count": 0,
            "competition_level": "Bilinmiyor",
            "price_analysis": {
                "min_price": 0,
                "max_price": 0,
                "avg_price": 0,
                "price_range": 0
            },
            "top_sellers": [],
            "popular_features": [],
            "raw_results": [],
            "timestamp": datetime.now().isoformat(),
            "error": "Rakip analizi yapılamadı - API bağlantısı kurulamadı"
        } 