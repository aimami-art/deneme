"""
PDF Document Model
PDF dosyalarını veritabanında saklamak için model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class PDFDocument(Base):
    """PDF Doküman modeli"""
    __tablename__ = "pdf_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    content_text = Column(Text)  # Extracted text
    chunk_count = Column(Integer, default=0)
    is_processed = Column(Boolean, default=False)
    is_embedded = Column(Boolean, default=False)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    embedded_at = Column(DateTime, nullable=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="pdf_documents")
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # JSON string for tags
    
    def __repr__(self):
        return f"<PDFDocument(id={self.id}, filename='{self.filename}', category='{self.category}')>"


class PDFChunk(Base):
    """PDF Chunk modeli - PDF'in parçalarını saklar"""
    __tablename__ = "pdf_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_document_id = Column(Integer, ForeignKey("pdf_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    
    # Vector embedding info
    vector_id = Column(String(100), nullable=True)  # Pinecone vector ID
    is_embedded = Column(Boolean, default=False)
    embedded_at = Column(DateTime, nullable=True)
    
    # Relationships
    pdf_document = relationship("PDFDocument", backref="chunks")
    
    def __repr__(self):
        return f"<PDFChunk(id={self.id}, pdf_id={self.pdf_document_id}, chunk_index={self.chunk_index})>"