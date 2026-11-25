from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int
    filename: str
    type: str
    etablissement: str = "IIT"
    parcours_id: Optional[int] = None
    size_bytes: int = 0
    mime_type: str = "application/octet-stream"
    status: str = "INDEXED"
    chunks_count: int = 1
    hash_content: str = ""
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: int
    status: str
    chunks_count: int = 1
    indexed_at: Optional[datetime] = None


class RAGSearchRequest(BaseModel):
    query: str = Field(..., description="Question ou terme de recherche sémantique")
    etablissement: Optional[str] = Field(None, description="Filtre IIT ou ISB")
    top_k: int = Field(3, ge=1, le=10)


class RAGSearchResultItem(BaseModel):
    document_id: int
    title: str
    page: Optional[int] = None
    score: float
    snippet: str


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResultItem]
