"""
Exchange Rate API Servisi
Döviz kuru bilgilerini almak için kullanılır
"""

import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.core.config import settings


class ExchangeRateService:
    """Exchange Rate API ile döviz kuru servisi"""
    
    def __init__(self):
        self.api_key = settings.EXCHANGERATE_API_KEY
        self.base_url = "https://v6.exchangerate-api.com/v6"
        self.cache = {}  # Basit in-memory cache
        self.cache_ttl = 3600  # 1 saat
    
    async def get_latest_rates(self, base_currency: str = "USD") -> Dict[str, Any]:
        """En güncel döviz kurlarını getir"""
        cache_key = f"latest_{base_currency}"
        
        # Cache kontrolü
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() < cached_data["expires_at"]:
                return cached_data["data"]
        
        try:
            url = f"{self.base_url}/{self.api_key}/latest/{base_currency}"
            response = await asyncio.to_thread(requests.get, url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache'e kaydet
                self.cache[cache_key] = {
                    "data": data,
                    "expires_at": datetime.now() + timedelta(seconds=self.cache_ttl)
                }
                
                return data
            else:
                print(f"❌ Exchange Rate API hatası: {response.status_code}")
                return self._get_fallback_rates(base_currency)
                
        except Exception as e:
            print(f"❌ Exchange Rate API bağlantı hatası: {str(e)}")
            return self._get_fallback_rates(base_currency)
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Para birimi dönüştürme"""
        try:
            rates_data = await self.get_latest_rates(from_currency)
            
            if rates_data["result"] == "success":
                conversion_rate = rates_data["conversion_rates"].get(to_currency)
                
                if conversion_rate:
                    converted_amount = amount * conversion_rate
                    
                    return {
                        "success": True,
                        "from": from_currency,
                        "to": to_currency,
                        "amount": amount,
                        "converted_amount": round(converted_amount, 2),
                        "rate": conversion_rate,
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {
                "success": False,
                "error": "Dönüşüm yapılamadı",
                "from": from_currency,
                "to": to_currency,
                "amount": amount
            }
            
        except Exception as e:
            print(f"❌ Para birimi dönüştürme hatası: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "from": from_currency,
                "to": to_currency,
                "amount": amount
            }
    
    async def get_supported_currencies(self) -> List[Dict[str, str]]:
        """Desteklenen para birimlerini getir"""
        try:
            url = f"{self.base_url}/{self.api_key}/codes"
            response = await asyncio.to_thread(requests.get, url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data["result"] == "success":
                    currencies = [
                        {"code": code, "name": name}
                        for code, name in data["supported_codes"]
                    ]
                    return currencies
            
            return self._get_fallback_currencies()
            
        except Exception as e:
            print(f"❌ Para birimleri alınırken hata: {str(e)}")
            return self._get_fallback_currencies()
    
    def _get_fallback_rates(self, base_currency: str = "USD") -> Dict[str, Any]:
        """API çalışmadığında kullanılacak fallback kurlar"""
        fallback_rates = {
            "USD": {"TRY": 30.5, "EUR": 0.92, "GBP": 0.79},
            "EUR": {"TRY": 33.2, "USD": 1.09, "GBP": 0.86},
            "TRY": {"USD": 0.033, "EUR": 0.03, "GBP": 0.026}
        }
        
        rates = fallback_rates.get(base_currency, {"USD": 1.0, "EUR": 0.92, "TRY": 30.5})
        
        return {
            "result": "success",
            "base_code": base_currency,
            "conversion_rates": rates,
            "time_last_update_utc": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "note": "Fallback veriler kullanılıyor - API bağlantısı kurulamadı"
        }
    
    def _get_fallback_currencies(self) -> List[Dict[str, str]]:
        """Fallback para birimleri listesi"""
        return [
            {"code": "USD", "name": "United States Dollar"},
            {"code": "EUR", "name": "Euro"},
            {"code": "TRY", "name": "Turkish Lira"},
            {"code": "GBP", "name": "British Pound"},
            {"code": "JPY", "name": "Japanese Yen"},
            {"code": "CNY", "name": "Chinese Yuan"},
            {"code": "RUB", "name": "Russian Ruble"},
            {"code": "AUD", "name": "Australian Dollar"},
            {"code": "CAD", "name": "Canadian Dollar"},
            {"code": "CHF", "name": "Swiss Franc"}
        ] 