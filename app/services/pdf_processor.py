"""
PDF Processing Service
PDF dosyalarını işleme ve chunk'lara bölme servisi
"""

import os
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

# PDF processing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pdfplumber
        PyPDF2 = None
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

from app.core.config import settings
from app.core.database import get_db
from app.models.pdf_document import PDFDocument, PDFChunk
from app.schemas.pdf_document import PDFDocumentCreate, PDFChunkCreate
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF işleme servisi"""
    
    def __init__(self):
        self.chunk_size = 2000  # Karakterde chunk boyutu (artırıldı)
        self.chunk_overlap = 300  # Overlap miktarı (artırıldı)
        self.upload_dir = "app/uploads/pdfs/"
        
        # Upload dizinini oluştur
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_uploaded_file(self, file_content: bytes, original_filename: str) -> str:
        """Yüklenen dosyayı kaydet"""
        try:
            # Unique filename oluştur
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Dosyayı kaydet
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"📁 PDF dosyası kaydedildi: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ Dosya kaydetme hatası: {e}")
            raise
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """PDF'den metin çıkar"""
        if not PDF_AVAILABLE:
            raise ValueError("PDF işleme kütüphanesi kurulu değil")
        
        try:
            text = ""
            
            if PyPDF2:
                # PyPDF2 kullan
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n[Sayfa {page_num + 1}]\n{page_text}\n"
            else:
                # pdfplumber kullan
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n[Sayfa {page_num + 1}]\n{page_text}\n"
            
            logger.info(f"📄 PDF metin çıkarıldı: {len(text)} karakter")
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ PDF metin çıkarma hatası: {e}")
            raise
    
    def _create_smart_chunk(self, text: str, page_num: int) -> tuple[str, str]:
        """Akıllı chunk oluştur - cümle sınırlarını ve anlam bütünlüğünü korur"""
        
        # Önce ideal chunk boyutunu al
        target_chunk = text[:self.chunk_size]
        
        # 1. Paragraf sınırında kes (en iyi)
        paragraph_breaks = [i for i, char in enumerate(target_chunk) if char == '\n' and i > self.chunk_size - 400]
        if paragraph_breaks:
            cut_point = max(paragraph_breaks)
            chunk_text = text[:cut_point]
            remaining_text = text[cut_point - self.chunk_overlap:]
            return chunk_text.strip(), remaining_text.strip()
        
        # 2. Cümle sonunda kes (iyi)
        sentence_ends = [i for i, char in enumerate(target_chunk) if char in '.!?' and i > self.chunk_size - 300]
        if sentence_ends:
            cut_point = max(sentence_ends) + 1
            chunk_text = text[:cut_point]
            remaining_text = text[cut_point - self.chunk_overlap:]
            return chunk_text.strip(), remaining_text.strip()
        
        # 3. Kelime sınırında kes (orta)
        words = target_chunk.split()
        if len(words) > 10:
            # Son 10 kelimeyi kontrol et
            word_positions = []
            current_pos = 0
            for i, word in enumerate(words[:-10]):
                current_pos += len(word) + 1  # +1 for space
                word_positions.append(current_pos)
            
            if word_positions:
                cut_point = word_positions[-1]
                chunk_text = text[:cut_point]
                remaining_text = text[cut_point - self.chunk_overlap:]
                return chunk_text.strip(), remaining_text.strip()
        
        # 4. Son çare: sabit boyutta kes
        chunk_text = text[:self.chunk_size]
        remaining_text = text[self.chunk_size - self.chunk_overlap:]
        return chunk_text.strip(), remaining_text.strip()
    
    async def create_chunks(self, text: str, pdf_document_id: int) -> List[PDFChunkCreate]:
        """Metni akıllı chunk'lara böl - sayfa sınırları ve cümle bütünlüğü korunur"""
        try:
            chunks = []
            chunk_index = 0
            
            # Sayfa bazlı bölme
            pages = text.split('[Sayfa ')
            current_text = ""
            current_page = 1
            
            for page_section in pages[1:]:  # İlk boş elementi atla
                # Sayfa numarasını çıkar
                if ']' in page_section:
                    page_content = page_section.split(']', 1)[1]
                    page_num = int(page_section.split(']')[0])
                else:
                    page_content = page_section
                    page_num = current_page
                
                # Sayfa içeriğini temizle
                page_content = page_content.strip()
                if not page_content:
                    continue
                    
                current_text += f" {page_content}" if current_text else page_content
                
                # Chunk boyutu kontrol et
                while len(current_text) >= self.chunk_size:
                    chunk_text, remaining_text = self._create_smart_chunk(current_text, page_num)
                    
                    # Chunk oluştur
                    chunk = PDFChunkCreate(
                        pdf_document_id=pdf_document_id,
                        chunk_index=chunk_index,
                        content=chunk_text.strip(),
                        page_number=page_num
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    
                    current_text = remaining_text
                
                current_page = page_num + 1
            
            # Kalan metni son chunk olarak ekle
            if current_text.strip():
                chunk = PDFChunkCreate(
                    pdf_document_id=pdf_document_id,
                    chunk_index=chunk_index,
                    content=current_text.strip(),
                    page_number=current_page - 1
                )
                chunks.append(chunk)
            
            logger.info(f"📝 {len(chunks)} chunk oluşturuldu")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Chunk oluşturma hatası: {e}")
            raise
    
    async def process_pdf(self, pdf_document_id: int, file_path: str, db: Session) -> Dict[str, Any]:
        """PDF'i tamamen işle"""
        start_time = datetime.now()
        
        try:
            # PDF dokümanını al
            pdf_doc = db.query(PDFDocument).filter(PDFDocument.id == pdf_document_id).first()
            if not pdf_doc:
                raise ValueError(f"PDF doküman bulunamadı: {pdf_document_id}")
            
            # Metin çıkar
            text = await self.extract_text_from_pdf(file_path)
            
            # PDF dokümanını güncelle
            pdf_doc.content_text = text
            pdf_doc.is_processed = True
            pdf_doc.processed_at = datetime.now()
            db.commit()
            
            # Chunk'ları oluştur
            chunks_data = await self.create_chunks(text, pdf_document_id)
            
            # Chunk'ları veritabanına kaydet
            saved_chunks = 0
            for chunk_data in chunks_data:
                chunk = PDFChunk(
                    pdf_document_id=chunk_data.pdf_document_id,
                    chunk_index=chunk_data.chunk_index,
                    content=chunk_data.content,
                    page_number=chunk_data.page_number
                )
                db.add(chunk)
                saved_chunks += 1
            
            # Chunk sayısını güncelle
            pdf_doc.chunk_count = saved_chunks
            db.commit()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": f"PDF başarıyla işlendi",
                "chunks_created": saved_chunks,
                "processing_time": processing_time,
                "text_length": len(text)
            }
            
            logger.info(f"✅ PDF işleme tamamlandı: {pdf_document_id} - {saved_chunks} chunk")
            return result
            
        except Exception as e:
            logger.error(f"❌ PDF işleme hatası: {e}")
            # Hata durumunda PDF'i işlenmemiş olarak işaretle
            try:
                pdf_doc = db.query(PDFDocument).filter(PDFDocument.id == pdf_document_id).first()
                if pdf_doc:
                    pdf_doc.is_processed = False
                    db.commit()
            except:
                pass
            
            raise
    
    async def get_categories(self, db: Session = None) -> List[str]:
        """Mevcut kategorileri al"""
        try:
            if db is None:
                db = next(get_db())
                should_close = True
            else:
                should_close = False
                
            categories = db.query(PDFDocument.category).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        except Exception as e:
            logger.error(f"❌ Kategori alma hatası: {e}")
            return []
        finally:
            if should_close and db:
                db.close()
    
    async def get_pdf_stats(self, user_id: int, db: Session = None) -> Dict[str, Any]:
        """PDF istatistikleri al"""
        try:
            if db is None:
                db = next(get_db())
                should_close = True
            else:
                should_close = False
            
            # Toplam dokümanblar
            total_docs = db.query(PDFDocument).filter(PDFDocument.user_id == user_id).count()
            
            # Toplam chunk'lar
            total_chunks = db.query(PDFChunk).join(PDFDocument).filter(
                PDFDocument.user_id == user_id
            ).count()
            
            # Embedded chunk'lar
            embedded_chunks = db.query(PDFChunk).join(PDFDocument).filter(
                PDFDocument.user_id == user_id,
                PDFChunk.is_embedded == True
            ).count()
            
            # Kategoriler
            categories = db.query(PDFDocument.category).filter(
                PDFDocument.user_id == user_id
            ).distinct().all()
            
            # Toplam boyut
            total_size = db.query(PDFDocument.file_size).filter(
                PDFDocument.user_id == user_id
            ).all()
            total_size_bytes = sum([size[0] for size in total_size])
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            # İşleme durumu
            processed_docs = db.query(PDFDocument).filter(
                PDFDocument.user_id == user_id,
                PDFDocument.is_processed == True
            ).count()
            
            return {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "categories": [cat[0] for cat in categories],
                "total_size_mb": round(total_size_mb, 2),
                "processing_status": {
                    "processed": processed_docs,
                    "pending": total_docs - processed_docs,
                    "embedding_progress": f"{embedded_chunks}/{total_chunks}" if total_chunks > 0 else "0/0"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ PDF istatistik hatası: {e}")
            return {}
        finally:
            if should_close and db:
                db.close()


# Global PDF Processor instance
pdf_processor = PDFProcessor()