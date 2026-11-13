from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)                  # pdf_programme, fiche_faq, brochure, page_web
    etablissement = Column(String(20), nullable=False)         # IIT, ISB
    parcours_id = Column(Integer, nullable=True)
    size_bytes = Column(Integer, nullable=False)               # Max 52428800 (50 Mo)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(30), default="UPLOADED", nullable=False) # UPLOADED, PARSING, INDEXED, FAILED
    chunks_count = Column(Integer, default=0)
    hash_content = Column(String(64), unique=True, index=True, nullable=False) # SHA-256
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    storage_path = Column(String(500), nullable=True)          # Chemin dans MinIO
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    indexed_at = Column(DateTime, nullable=True)
