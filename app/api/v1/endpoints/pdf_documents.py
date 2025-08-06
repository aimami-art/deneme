"""
PDF Documents API Endpoints
PDF yükleme, işleme ve yönetim endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime

from app.services.auth_service import AuthService
from app.models.user import User
from app.models.pdf_document import PDFDocument, PDFChunk
from app.core.admin import get_admin_user
from app.schemas.pdf_document import (
    PDFDocumentResponse, PDFUploadResponse, PDFProcessResponse,
    PDFStatsResponse, PDFChunkResponse
)
from app.services.pdf_processor import pdf_processor
from app.services.rag_engine import RAGEmbeddingEngine
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """PDF dosyası yükle"""
    try:
        # Dosya tipi kontrolü
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Sadece PDF dosyaları yüklenebilir"
            )
        
        # Dosya boyutu kontrolü (50MB limit)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=400,
                detail="Dosya boyutu 50MB'dan büyük olamaz"
            )
        
        # Dosyayı kaydet
        file_path = await pdf_processor.save_uploaded_file(file_content, file.filename)
        
        # Tags'i JSON'a çevir
        tags_json = None
        if tags:
            try:
                tags_list = json.loads(tags) if tags.startswith('[') else tags.split(',')
                tags_json = json.dumps(tags_list)
            except:
                tags_json = tags
        
        # Veritabanına kaydet
        pdf_doc = PDFDocument(
            filename=file.filename,
            original_filename=file.filename,
            category=category.strip(),
            file_path=file_path,
            file_size=len(file_content),
            description=description,
            tags=tags_json,
            user_id=current_user.id
        )
        
        db.add(pdf_doc)
        db.commit()
        db.refresh(pdf_doc)
        
        # Background task olarak PDF işleme başlat
        background_tasks.add_task(process_pdf_background, pdf_doc.id, file_path)
        
        logger.info(f"📁 PDF yüklendi: {file.filename} (ID: {pdf_doc.id})")
        
        return PDFUploadResponse(
            success=True,
            message="PDF başarıyla yüklendi ve işleme alındı",
            pdf_document_id=pdf_doc.id,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF yükleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_pdf_background(pdf_document_id: int, file_path: str):
    """Background task olarak PDF işle"""
    try:
        await pdf_processor.process_pdf(pdf_document_id, file_path)
        logger.info(f"✅ Background PDF işleme tamamlandı: {pdf_document_id}")
    except Exception as e:
        logger.error(f"❌ Background PDF işleme hatası: {e}")


@router.get("/list", response_model=List[PDFDocumentResponse])
async def list_pdf_documents(
    category: Optional[str] = None,
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """Kullanıcının PDF dokümanblarını listele"""
    try:
        query = db.query(PDFDocument).filter(PDFDocument.user_id == current_user.id)
        
        if category:
            query = query.filter(PDFDocument.category == category)
        
        pdf_docs = query.order_by(PDFDocument.uploaded_at.desc()).all()
        
        return pdf_docs
        
    except Exception as e:
        logger.error(f"❌ PDF listeleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pdf_id}", response_model=PDFDocumentResponse)
async def get_pdf_document(
    pdf_id: int,
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """PDF doküman detayını al"""
    try:
        pdf_doc = db.query(PDFDocument).filter(
            PDFDocument.id == pdf_id,
            PDFDocument.user_id == current_user.id
        ).first()
        
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF doküman bulunamadı")
        
        return pdf_doc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF detay alma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pdf_id}/chunks", response_model=List[PDFChunkResponse])
async def get_pdf_chunks(
    pdf_id: int,
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """PDF chunk'larını al"""
    try:
        # PDF'in kullanıcıya ait olduğunu kontrol et
        pdf_doc = db.query(PDFDocument).filter(
            PDFDocument.id == pdf_id,
            PDFDocument.user_id == current_user.id
        ).first()
        
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF doküman bulunamadı")
        
        chunks = db.query(PDFChunk).filter(
            PDFChunk.pdf_document_id == pdf_id
        ).order_by(PDFChunk.chunk_index).all()
        
        return chunks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF chunk alma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pdf_id}/process", response_model=PDFProcessResponse)
async def process_pdf_manual(
    pdf_id: int,
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """PDF'i manuel olarak işle"""
    try:
        # PDF'in kullanıcıya ait olduğunu kontrol et
        pdf_doc = db.query(PDFDocument).filter(
            PDFDocument.id == pdf_id,
            PDFDocument.user_id == current_user.id
        ).first()
        
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF doküman bulunamadı")
        
        if pdf_doc.is_processed:
            return PDFProcessResponse(
                success=True,
                message="PDF zaten işlenmiş",
                chunks_created=pdf_doc.chunk_count,
                processing_time=0.0
            )
        
        # PDF'i işle
        result = await pdf_processor.process_pdf(pdf_id, pdf_doc.file_path, db)
        
        return PDFProcessResponse(
            success=result["success"],
            message=result["message"],
            chunks_created=result["chunks_created"],
            processing_time=result["processing_time"]
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        if "PDF işleme kütüphanesi kurulu değil" in str(e):
            raise HTTPException(
                status_code=400, 
                detail="PDF işleme kütüphaneleri (PyPDF2, pdfplumber) yüklü değil. Lütfen gerekli kütüphaneleri yükleyin."
            )
        logger.error(f"❌ PDF manuel işleme hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ PDF manuel işleme hatası: {e}")
        raise HTTPException(status_code=500, detail=f"PDF işleme hatası: {str(e)}")


@router.delete("/{pdf_id}")
async def delete_pdf_document(
    pdf_id: int,
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """PDF dokümanbı sil"""
    try:
        # PDF'in kullanıcıya ait olduğunu kontrol et
        pdf_doc = db.query(PDFDocument).filter(
            PDFDocument.id == pdf_id,
            PDFDocument.user_id == current_user.id
        ).first()
        
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF doküman bulunamadı")
        
        # Chunk'ları sil
        db.query(PDFChunk).filter(PDFChunk.pdf_document_id == pdf_id).delete()
        
        # PDF dokümanbı sil
        db.delete(pdf_doc)
        db.commit()
        
        # Dosyayı diskten sil
        try:
            import os
            if os.path.exists(pdf_doc.file_path):
                os.remove(pdf_doc.file_path)
        except:
            pass
        
        logger.info(f"🗑️ PDF silindi: {pdf_id}")
        
        return {"success": True, "message": "PDF başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF silme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview", response_model=PDFStatsResponse)
async def get_pdf_stats(
    current_user: User = Depends(AuthService.get_current_user)
):
    """PDF istatistiklerini al"""
    try:
        stats = await pdf_processor.get_pdf_stats(current_user.id)
        
        return PDFStatsResponse(
            total_documents=stats.get("total_documents", 0),
            total_chunks=stats.get("total_chunks", 0),
            embedded_chunks=stats.get("embedded_chunks", 0),
            categories=stats.get("categories", []),
            total_size_mb=stats.get("total_size_mb", 0.0),
            processing_status=stats.get("processing_status", {})
        )
        
    except Exception as e:
        logger.error(f"❌ PDF istatistik hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
async def get_categories(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Mevcut kategorileri al"""
    try:
        categories = await pdf_processor.get_categories()
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"❌ Kategori alma hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pdf_id}/embed")
async def embed_pdf_to_vector_db(
    pdf_id: int,
    current_user: User = Depends(get_admin_user),  # Admin only
    db: Session = Depends(get_db)
):
    """PDF'i vector database'e embed et"""
    try:
        # PDF'in kullanıcıya ait olduğunu kontrol et
        pdf_doc = db.query(PDFDocument).filter(
            PDFDocument.id == pdf_id,
            PDFDocument.user_id == current_user.id
        ).first()
        
        if not pdf_doc:
            raise HTTPException(status_code=404, detail="PDF doküman bulunamadı")
        
        if not pdf_doc.is_processed:
            raise HTTPException(status_code=400, detail="PDF önce işlenmeli")
        
        # RAG Engine ile embed et
        rag_engine = RAGEmbeddingEngine()
        result = await rag_engine.embed_pdf_chunks(current_user.id, pdf_id)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "embedded_count": result["embedded_count"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ PDF embedding hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed-all")
async def embed_all_pdfs(
    current_user: User = Depends(AuthService.get_current_user)
):
    """Kullanıcının tüm PDF'lerini vector database'e embed et"""
    try:
        rag_engine = RAGEmbeddingEngine()
        result = await rag_engine.embed_pdf_chunks(current_user.id)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "embedded_count": result["embedded_count"]
        }
        
    except Exception as e:
        logger.error(f"❌ Toplu PDF embedding hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{category}")
async def search_pdf_by_category(
    category: str,
    query: str,
    top_k: int = 5,
    current_user: User = Depends(AuthService.get_current_user)
):
    """Kategori bazlı PDF arama"""
    try:
        rag_engine = RAGEmbeddingEngine()
        results = await rag_engine.search_pdf_by_category(category, query, top_k)
        
        return {
            "success": True,
            "category": category,
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ PDF kategori arama hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))