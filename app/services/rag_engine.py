"""
RAG & Embedding Engine
Vector tabanlı strateji arama ve retrieval sistemi
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try-except imports for graceful degradation
try:
    # LangChain imports
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    from langchain_community.vectorstores import Pinecone as PineconeVectorStore
    from langchain.chains import RetrievalQA
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    LANGCHAIN_AVAILABLE = True
    logger.info("✅ LangChain kütüphaneleri yüklendi")
except ImportError as e:
    logger.warning(f"⚠️ LangChain import hatası: {e}")
    LANGCHAIN_AVAILABLE = False

try:
    # Pinecone imports
    import pinecone
    PINECONE_AVAILABLE = True
    logger.info("✅ Pinecone kütüphanesi yüklendi")
except ImportError as e:
    logger.warning(f"⚠️ Pinecone import hatası: {e}")
    PINECONE_AVAILABLE = False

try:
    # Sentence Transformers (fallback)
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("✅ Sentence Transformers kütüphanesi yüklendi")
except ImportError as e:
    logger.warning(f"⚠️ Sentence Transformers import hatası: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.core.config import settings
from app.models.strategy import Strategy
from app.models.pdf_document import PDFDocument, PDFChunk
from app.models.product import Product
from sqlalchemy.orm import Session


class RAGEmbeddingEngine:
    """RAG & Embedding Engine - Vector tabanlı strateji sistemi"""
    
    def __init__(self):
        self.pinecone_client = None
        self.pinecone_index = None
        self.vector_store = None
        self.embeddings = None
        self.fallback_model = None
        self.text_splitter = None
        self.pinecone_available = False  # Pinecone durumu
        
        # LangChain text splitter'ı başlat
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
        
        # Pinecone index ayarları
        self.index_name = "ai-sales-strategies"
        self.dimension = 768  # Sentence-BERT embedding boyutu
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Servisleri başlat"""
        try:
            # Pinecone istemcisini başlat (Yeni Global API)
            if PINECONE_AVAILABLE and settings.PINECONE_API_KEY:
                try:
                    from pinecone import Pinecone
                    
                    # Yeni Global API kullan
                    self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
                    logger.info("✅ Pinecone Global API istemcisi başlatıldı")
                    
                    # Index'i kontrol et veya oluştur
                    self._ensure_index_exists()
                    self.pinecone_available = True
                except Exception as e:
                    logger.error(f"❌ Pinecone başlatma hatası: {e}")
                    self.pinecone_client = None
            else:
                logger.warning("⚠️ Pinecone kütüphanesi yok veya API anahtarı bulunamadı")
            
            # Embedding modellerini başlat
            self._initialize_embeddings()
            
        except Exception as e:
            logger.error(f"❌ RAG Engine başlatma hatası: {e}")
    
    def _ensure_index_exists(self):
        """Pinecone index'inin var olduğundan emin ol"""
        try:
            # Mevcut index'leri listele (Yeni Global API)
            existing_indexes = [index.name for index in self.pinecone_client.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"📝 Pinecone index oluşturuluyor: {self.index_name}")
                
                # Yeni index oluştur (Yeni Global API)
                from pinecone import ServerlessSpec
                
                self.pinecone_client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"✅ Pinecone index oluşturuldu: {self.index_name}")
            else:
                logger.info(f"✅ Pinecone index mevcut: {self.index_name}")
            
            # Index'e bağlan (Yeni Global API)
            self.pinecone_index = self.pinecone_client.Index(self.index_name)
                
        except Exception as e:
            logger.error(f"❌ Pinecone index kontrol hatası: {e}")
            self.pinecone_index = None
    
    def _initialize_embeddings(self):
        """Embedding modellerini başlat"""
        try:
            # Önce Google Gemini embeddings'i dene
            if LANGCHAIN_AVAILABLE and settings.GEMINI_API_KEY:
                try:
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/embedding-001",
                        google_api_key=settings.GEMINI_API_KEY
                    )
                    logger.info("✅ Google Gemini embeddings başlatıldı")
                except Exception as e:
                    logger.warning(f"⚠️ Gemini embeddings hatası: {e}")
                    self.embeddings = None
            
            # Fallback: Sentence Transformers
            if not self.embeddings and SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    self.fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("✅ Sentence Transformers fallback model yüklendi")
                except Exception as e:
                    logger.error(f"❌ Sentence Transformers hatası: {e}")
            
            # Son durum kontrolü
            if not self.embeddings and not self.fallback_model:
                logger.warning("⚠️ Hiçbir embedding modeli yüklenemedi - fallback mode aktif")
                    
        except Exception as e:
            logger.error(f"❌ Embedding modelleri başlatma hatası: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Metni vector'e dönüştür"""
        try:
            if self.embeddings:
                # Google Gemini embeddings kullan
                embedding = await asyncio.to_thread(
                    self.embeddings.embed_query, text
                )
                return embedding
            elif self.fallback_model:
                # Sentence Transformers fallback
                embedding = await asyncio.to_thread(
                    self.fallback_model.encode, text
                )
                return embedding.tolist()
            else:
                logger.warning("⚠️ Embedding modeli yok - demo vector döndürülüyor")
                # Son çare: normalize edilmiş rastgele vector (sadece test için)
                import random
                import math
                vector = [random.gauss(0, 1) for _ in range(self.dimension)]
                # Normalize et
                magnitude = math.sqrt(sum(x*x for x in vector))
                return [x/magnitude for x in vector]
                
        except Exception as e:
            logger.error(f"❌ Embedding hatası: {e}")
            # Son çare: normalize edilmiş rastgele vector
            import random
            import math
            vector = [random.gauss(0, 1) for _ in range(self.dimension)]
            magnitude = math.sqrt(sum(x*x for x in vector))
            return [x/magnitude for x in vector]
    
    async def _embed_text(self, text: str) -> List[float]:
        """Private method for embedding text (alias for embed_text)"""
        return await self.embed_text(text)
    
    async def add_strategy_to_vector_db(self, strategy: Strategy, product: Product, db: Session) -> bool:
        """Stratejiyi vector veritabanına ekle"""
        try:
            if not self.pinecone_index:
                logger.warning("❌ Pinecone index mevcut değil")
                return False
            
            # Strategy nesnesini current session'a merge et
            try:
                strategy = db.merge(strategy)
            except Exception as e:
                logger.warning(f"Strategy session merge hatası: {e}")
            
            # Strateji metnini chunk'lara böl
            strategy_text = f"{strategy.title or 'Strateji'}\n\n{strategy.content or 'İçerik yok'}"
            
            # Text splitter varsa kullan, yoksa basit bölme yap
            if self.text_splitter:
                chunks = self.text_splitter.split_text(strategy_text)
            else:
                # Basit chunk bölme (1000 karakter)
                chunk_size = 1000
                chunks = [strategy_text[i:i+chunk_size] for i in range(0, len(strategy_text), chunk_size)]
            
            # Her chunk için vector oluştur ve kaydet
            vectors_to_upsert = []
            
            for i, chunk in enumerate(chunks):
                # Embedding oluştur
                embedding = await self.embed_text(chunk)
                
                # Metadata hazırla - product nesnesini session'dan refresh et
                try:
                    # Product'ı current session'a merge et
                    product = db.merge(product)
                    product_name = product.name
                    product_category = product.category
                except Exception as e:
                    logger.warning(f"Product bilgisi alınamadı: {e}")
                    product_name = f"Product_{strategy.product_id}"
                    product_category = "unknown"
                
                metadata = {
                    "strategy_id": strategy.id,
                    "product_id": strategy.product_id,
                    "user_id": strategy.user_id,
                    "product_name": product_name,
                    "product_category": product_category,
                    "strategy_title": strategy.title or "Strateji",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "text": chunk,
                    "confidence_score": float(strategy.confidence_score or 0.8),
                    "expected_roi": float(strategy.expected_roi or 0.15),
                    "implementation_difficulty": strategy.implementation_difficulty or "medium",
                    "created_at": strategy.created_at.isoformat() if strategy.created_at else datetime.now().isoformat(),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Vector ID oluştur
                vector_id = f"strategy_{strategy.id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                
                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Pinecone'a yükle
            await asyncio.to_thread(
                self.pinecone_index.upsert, vectors=vectors_to_upsert
            )
            
            logger.info(f"✅ Strateji vector DB'ye eklendi: {strategy.title} ({len(chunks)} chunk)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector DB'ye ekleme hatası: {e}")
            return False
    
    async def search_similar_strategies(
        self, 
        query: str, 
        user_id: int,
        product_category: str = None,
        top_k: int = 5,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Benzer stratejileri ara"""
        try:
            if not self.pinecone_index:
                logger.warning("❌ Pinecone index mevcut değil - fallback sonuçlar döndürülüyor")
                return self._get_fallback_search_results(query, top_k)
            
            # Query embedding'i oluştur
            query_embedding = await self.embed_text(query)
            
            # Filter oluştur
            filter_dict = {"user_id": user_id}
            if product_category:
                filter_dict["product_category"] = product_category
            
            # Vector arama yap
            search_results = await asyncio.to_thread(
                self.pinecone_index.query,
                vector=query_embedding,
                top_k=top_k * 2,  # Daha fazla sonuç al, sonra filtrele
                include_metadata=True,
                filter=filter_dict
            )
            
            # Sonuçları işle
            similar_strategies = []
            seen_strategy_ids = set()
            
            for match in search_results['matches']:
                if match['score'] >= min_score:
                    strategy_id = match['metadata'].get("strategy_id")
                    
                    # Aynı stratejiyi birden fazla ekleme
                    if strategy_id not in seen_strategy_ids:
                        seen_strategy_ids.add(strategy_id)
                        
                        similar_strategies.append({
                            "strategy_id": strategy_id,
                            "product_id": match['metadata'].get("product_id"),
                            "product_name": match['metadata'].get("product_name"),
                            "product_category": match['metadata'].get("product_category"),
                            "strategy_title": match['metadata'].get("strategy_title"),
                            "similarity_score": float(match['score']),
                            "confidence_score": match['metadata'].get("confidence_score", 0.0),
                            "expected_roi": match['metadata'].get("expected_roi", 0.0),
                            "implementation_difficulty": match['metadata'].get("implementation_difficulty", "medium"),
                            "text_snippet": match['metadata'].get("text", "")[:200] + "...",
                            "created_at": match['metadata'].get("created_at"),
                            "vector_id": match['id']
                        })
            
            # Similarity score'a göre sırala
            similar_strategies.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            logger.info(f"🔍 Vector arama tamamlandı: {len(similar_strategies)} benzer strateji bulundu")
            return similar_strategies[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Vector arama hatası: {e}")
            return self._get_fallback_search_results(query, top_k)
    
    async def generate_rag_response(
        self,
        question: str,
        user_id: int,
        product_context: Dict[str, Any] = None,
        max_context_length: int = 3000
    ) -> Dict[str, Any]:
        """RAG ile soru-cevap sistemi"""
        try:
            # İlgili stratejileri ara
            product_category = product_context.get("category") if product_context else None
            similar_strategies = await self.search_similar_strategies(
                query=question,
                user_id=user_id,
                product_category=product_category,
                top_k=3,
                min_score=0.6
            )
            
            if not similar_strategies:
                return self._get_fallback_rag_response(question)
            
            # Context oluştur
            context_parts = []
            sources = []
            
            for strategy in similar_strategies:
                context_part = f"""
                Strateji: {strategy['strategy_title']}
                Ürün: {strategy['product_name']} ({strategy['product_category']})
                ROI: {strategy['expected_roi']}%
                Zorluk: {strategy['implementation_difficulty']}
                İçerik: {strategy['text_snippet']}
                """
                context_parts.append(context_part.strip())
                sources.append({
                    "strategy_id": strategy["strategy_id"],
                    "title": strategy["strategy_title"],
                    "product_name": strategy["product_name"],
                    "similarity_score": strategy["similarity_score"]
                })
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Context'i kısalt (gerekirse)
            if len(context) > max_context_length:
                context = context[:max_context_length] + "..."
            
            # Gemini ile cevap oluştur
            if settings.GEMINI_API_KEY:
                prompt = f"""
                Aşağıdaki strateji örneklerini kullanarak soruyu cevapla:
                
                CONTEXT:
                {context}
                
                SORU: {question}
                
                Lütfen:
                1. Verilen strateji örneklerinden yararlanarak kapsamlı bir cevap ver
                2. Somut öneriler ve eylem planları sun
                3. Mümkünse ROI ve uygulama zorluğu hakkında bilgi ver
                4. Türkçe olarak, profesyonel ve anlaşılır bir dilde cevapla
                
                CEVAP:
                """
                
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    response = await asyncio.to_thread(model.generate_content, prompt)
                    answer = response.text
                    
                    return {
                        "answer": answer,
                        "sources": sources,
                        "confidence": min(0.9, sum(s["similarity_score"] for s in similar_strategies) / len(similar_strategies)),
                        "context_used": len(context_parts)
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Gemini RAG hatası: {e}")
            
            # Fallback: Basit template cevap
            answer = f"""
            Benzer stratejilerinize dayanarak şu önerileri sunabilirim:
            
            {chr(10).join([f"• {s['strategy_title']} - ROI: {s['expected_roi']}%" for s in similar_strategies[:2]])}
            
            Bu stratejileri inceleyerek yeni yaklaşımlar geliştirebilirsiniz.
            """
            
            return {
                "answer": answer.strip(),
                "sources": sources,
                "confidence": 0.7,
                "context_used": len(context_parts)
            }
            
        except Exception as e:
            logger.error(f"❌ RAG response hatası: {e}")
            return self._get_fallback_rag_response(question)
    
    async def update_strategy_in_vector_db(self, strategy: Strategy, product: Product, db: Session) -> bool:
        """Vector DB'deki stratejiyi güncelle"""
        try:
            # Önce eski kayıtları sil
            await self.delete_strategy_from_vector_db(strategy.id)
            
            # Sonra yeni kayıt ekle
            return await self.add_strategy_to_vector_db(strategy, product, db)
            
        except Exception as e:
            logger.error(f"❌ Vector DB güncelleme hatası: {e}")
            return False
    
    async def delete_strategy_from_vector_db(self, strategy_id: int) -> bool:
        """Stratejiyi vector DB'den sil"""
        try:
            if not self.pinecone_index:
                logger.warning("❌ Pinecone index mevcut değil")
                return False
            
            # Strategy ID'ye göre tüm chunk'ları bul ve sil
            # Pinecone'da metadata ile delete yapmak için önce query yapmamız gerekiyor
            query_result = await asyncio.to_thread(
                self.pinecone_index.query,
                vector=[0.0] * self.dimension,  # Dummy vector
                top_k=1000,  # Yüksek limit
                include_metadata=True,
                filter={"strategy_id": strategy_id}
            )
            
            # Bulunan vector ID'lerini sil
            vector_ids = [match.id for match in query_result['matches']]
            
            if vector_ids:
                await asyncio.to_thread(self.pinecone_index.delete, ids=vector_ids)
                logger.info(f"✅ Vector DB'den silindi: Strategy {strategy_id} ({len(vector_ids)} chunk)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector DB'den silme hatası: {e}")
            return False
    
    async def get_vector_db_stats(self, user_id: int = None) -> Dict[str, Any]:
        """Vector DB istatistikleri"""
        try:
            if not self.pinecone_index:
                return {
                    "total_vectors": 0,
                    "index_fullness": 0.0,
                    "dimension": self.dimension,
                    "index_name": "N/A (Pinecone bağlantısı yok)",
                    "error": "Pinecone index mevcut değil"
                }
            
            # Index istatistikleri
            stats = await asyncio.to_thread(self.pinecone_index.describe_index_stats)
            
            result = {
                "total_vectors": stats.get('total_vector_count', 0),
                "index_fullness": stats.get('index_fullness', 0.0),
                "dimension": stats.get('dimension', self.dimension),
                "index_name": self.index_name
            }
            
            # Kullanıcı özel istatistikler
            if user_id:
                user_query = await asyncio.to_thread(
                    self.pinecone_index.query,
                    vector=[0.0] * self.dimension,
                    top_k=1,
                    include_metadata=True,
                    filter={"user_id": user_id}
                )
                
                # Kullanıcının toplam vector sayısını tahmin et (yaklaşık)
                if user_query.get('matches'):
                    result["user_vectors_sample"] = len(user_query['matches'])
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Vector DB stats hatası: {e}")
            return {"error": str(e)}
    
    def _get_fallback_search_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Pinecone yokken demo arama sonuçları"""
        demo_results = [
            {
                "strategy_id": None,  # Demo için None
                "product_id": 1,
                "product_name": "Demo Ürün",
                "product_category": "Teknoloji",
                "strategy_title": f"Demo Strateji: {query[:30]}...",
                "similarity_score": 0.85,
                "confidence_score": 0.8,
                "expected_roi": 25.0,
                "implementation_difficulty": "medium",
                "text_snippet": f"Bu, '{query}' aramanız için demo bir strateji örneğidir. Gerçek sonuçlar için Pinecone vector DB'yi kurun.",
                "created_at": datetime.now().isoformat(),
                "vector_id": "demo_vector_1"
            }
        ]
        
        logger.info(f"🔄 Demo arama sonuçları döndürülüyor: {query}")
        return demo_results[:top_k]
    
    def _get_fallback_rag_response(self, question: str) -> Dict[str, Any]:
        """Pinecone yokken demo RAG cevabı"""
        return {
            "answer": f"""Bu, '{question}' sorunuz için demo bir cevaptır. 

Gerçek AI destekli cevaplar almak için:
1. Pinecone index'inizi oluşturun
2. Stratejilerinizi vector DB'ye ekleyin
3. RAG sisteminin tam özelliklerinden yararlanın

Demo modunda çalışıyorsunuz.""",
            "sources": [],
            "confidence": 0.5,
            "context_used": 0
        }
    
    # ==================== PDF CATEGORY-BASED SEARCH ====================
    
    async def search_pdf_by_category(self, category: str, query: str, top_k: int = 3, min_score: float = 0.6) -> List[Dict[str, Any]]:
        """Kategori bazlı PDF chunk arama (admin PDF'lerinden)"""
        try:
            if not self.pinecone_available:
                return self._fallback_pdf_search(category, query)
            
            # Admin user ID'sini al
            from app.core.admin import get_admin_user_id
            from app.core.database import get_db
            db = next(get_db())
            admin_user_id = get_admin_user_id(db)
            db.close()
            
            if not admin_user_id:
                logger.warning("❌ Admin kullanıcı bulunamadı, PDF arama atlanıyor")
                return self._fallback_pdf_search(category, query)
            
            # Query'yi embed et
            query_vector = await self._embed_text(query)
            if not query_vector:
                return self._fallback_pdf_search(category, query)
            
            # Pinecone'da arama - category ve admin user_id filter ile
            search_results = self.pinecone_index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter={
                    "type": "pdf_chunk",
                    "category": category,
                    "user_id": admin_user_id  # Sadece admin'in PDF'leri
                }
            )
            
            results = []
            for match in search_results.matches:
                if match.score >= min_score:
                    results.append({
                        "chunk_id": match.metadata.get("chunk_id"),
                        "pdf_document_id": match.metadata.get("pdf_document_id"),
                        "content": match.metadata.get("content", ""),
                        "page_number": match.metadata.get("page_number"),
                        "category": match.metadata.get("category"),
                        "filename": match.metadata.get("filename"),
                        "score": float(match.score)
                    })
            
            logger.info(f"🔍 PDF kategorisi '{category}' için {len(results)} sonuç bulundu")
            return results
            
        except Exception as e:
            logger.error(f"❌ PDF kategori arama hatası: {e}")
            return self._fallback_pdf_search(category, query)
    
    async def embed_pdf_chunks(self, user_id: int, pdf_document_id: Optional[int] = None) -> Dict[str, Any]:
        """PDF chunk'larını Pinecone'a embed et"""
        try:
            if not self.pinecone_available:
                return {
                    "success": False,
                    "message": "Pinecone mevcut değil",
                    "embedded_count": 0
                }
            
            from app.core.database import get_db
            db: Session = next(get_db())
            
            # Embed edilecek chunk'ları al
            query = db.query(PDFChunk).join(PDFDocument).filter(
                PDFDocument.user_id == user_id,
                PDFChunk.is_embedded == False
            )
            
            if pdf_document_id:
                query = query.filter(PDFDocument.id == pdf_document_id)
            
            chunks = query.all()
            
            if not chunks:
                return {
                    "success": True,
                    "message": "Embed edilecek chunk bulunamadı",
                    "embedded_count": 0
                }
            
            embedded_count = 0
            batch_size = 50  # Batch processing
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                vectors_to_upsert = []
                
                for chunk in batch_chunks:
                    # Chunk'ı embed et
                    vector = await self._embed_text(chunk.content)
                    if not vector:
                        continue
                    
                    # Vector ID oluştur
                    vector_id = f"pdf_chunk_{chunk.id}_{uuid.uuid4().hex[:8]}"
                    
                    # Metadata hazırla
                    metadata = {
                        "type": "pdf_chunk",
                        "chunk_id": chunk.id,
                        "pdf_document_id": chunk.pdf_document_id,
                        "content": chunk.content[:1000],  # İlk 1000 karakter
                        "page_number": chunk.page_number,
                        "category": chunk.pdf_document.category,
                        "filename": chunk.pdf_document.filename,
                        "user_id": user_id,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    vectors_to_upsert.append({
                        "id": vector_id,
                        "values": vector,
                        "metadata": metadata
                    })
                    
                    # Chunk'ı embedded olarak işaretle
                    chunk.vector_id = vector_id
                    chunk.is_embedded = True
                    chunk.embedded_at = datetime.utcnow()
                    embedded_count += 1
                
                # Batch'i Pinecone'a gönder
                if vectors_to_upsert:
                    self.pinecone_index.upsert(vectors=vectors_to_upsert)
                    logger.info(f"📤 {len(vectors_to_upsert)} PDF chunk Pinecone'a gönderildi")
            
            # Veritabanını güncelle
            db.commit()
            db.close()
            
            return {
                "success": True,
                "message": f"{embedded_count} PDF chunk başarıyla embed edildi",
                "embedded_count": embedded_count
            }
            
        except Exception as e:
            logger.error(f"❌ PDF chunk embedding hatası: {e}")
            return {
                "success": False,
                "message": f"Embedding hatası: {str(e)}",
                "embedded_count": 0
            }
    
    async def get_pdf_context_for_strategy(self, category: str, product_name: str, top_k: int = 5) -> str:
        """Strateji oluşturma için kategori bazlı PDF context al"""
        try:
            # İlgili PDF chunk'larını ara
            query = f"{category} {product_name} satış stratejisi"
            pdf_chunks = await self.search_pdf_by_category(category, query, top_k=top_k)
            
            if not pdf_chunks:
                return ""
            
            # Context metni oluştur
            context_parts = []
            for i, chunk in enumerate(pdf_chunks, 1):
                context_parts.append(f"""
[Kaynak {i}: {chunk['filename']} - Sayfa {chunk.get('page_number', '?')}]
{chunk['content']}
""")
            
            full_context = "\n".join(context_parts)
            logger.info(f"📚 {category} kategorisi için {len(pdf_chunks)} chunk'tan context oluşturuldu")
            
            return full_context
            
        except Exception as e:
            logger.error(f"❌ PDF context alma hatası: {e}")
            return ""
    
    def _fallback_pdf_search(self, category: str, query: str) -> List[Dict[str, Any]]:
        """PDF arama fallback"""
        return [
            {
                "chunk_id": None,
                "pdf_document_id": None,
                "content": f"Demo: {category} kategorisinde '{query}' ile ilgili strateji örnekleri burada görünecek. Pinecone bağlantısı kurulduktan sonra gerçek sonuçlar gelecek.",
                "page_number": 1,
                "category": category,
                "filename": "demo_strategy.pdf",
                "score": 0.7
            }
        ] 