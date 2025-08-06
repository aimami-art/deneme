"""
PDF Document Schemas
PDF dosyaları için Pydantic şemaları
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PDFDocumentBase(BaseModel):
    """PDF doküman base şeması"""
    filename: str = Field(..., description="Dosya adı")
    category: str = Field(..., description="Kategori")
    description: Optional[str] = Field(None, description="Açıklama")
    tags: Optional[str] = Field(None, description="Etiketler (JSON)")


class PDFDocumentCreate(PDFDocumentBase):
    """PDF doküman oluşturma şeması"""
    original_filename: str = Field(..., description="Orijinal dosya adı")
    file_path: str = Field(..., description="Dosya yolu")
    file_size: int = Field(..., description="Dosya boyutu (bytes)")
    content_text: Optional[str] = Field(None, description="Çıkarılan metin")


class PDFDocumentUpdate(BaseModel):
    """PDF doküman güncelleme şeması"""
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None


class PDFDocumentResponse(PDFDocumentBase):
    """PDF doküman yanıt şeması"""
    id: int
    original_filename: str
    file_size: int
    chunk_count: int
    is_processed: bool
    is_embedded: bool
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    embedded_at: Optional[datetime] = None
    user_id: int

    class Config:
        from_attributes = True


class PDFChunkBase(BaseModel):
    """PDF chunk base şeması"""
    content: str = Field(..., description="Chunk içeriği")
    page_number: Optional[int] = Field(None, description="Sayfa numarası")


class PDFChunkCreate(PDFChunkBase):
    """PDF chunk oluşturma şeması"""
    pdf_document_id: int = Field(..., description="PDF doküman ID")
    chunk_index: int = Field(..., description="Chunk sırası")


class PDFChunkResponse(PDFChunkBase):
    """PDF chunk yanıt şeması"""
    id: int
    pdf_document_id: int
    chunk_index: int
    vector_id: Optional[str] = None
    is_embedded: bool
    embedded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PDFUploadRequest(BaseModel):
    """PDF yükleme request şeması"""
    category: str = Field(..., description="Kategori")
    description: Optional[str] = Field(None, description="Açıklama")
    tags: Optional[List[str]] = Field(None, description="Etiketler")


class PDFUploadResponse(BaseModel):
    """PDF yükleme yanıt şeması"""
    success: bool
    message: str
    pdf_document_id: Optional[int] = None
    filename: Optional[str] = None


class PDFProcessResponse(BaseModel):
    """PDF işleme yanıt şeması"""
    success: bool
    message: str
    chunks_created: int
    processing_time: float


class PDFEmbedResponse(BaseModel):
    """PDF embedding yanıt şeması"""
    success: bool
    message: str
    embedded_chunks: int
    embedding_time: float


class PDFStatsResponse(BaseModel):
    """PDF istatistik yanıt şeması"""
    total_documents: int
    total_chunks: int
    embedded_chunks: int
    categories: List[str]
    total_size_mb: float
    processing_status: dict