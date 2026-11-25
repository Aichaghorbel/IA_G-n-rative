from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Code métier d'erreur (ex: AUTH_001, CANDIDATE_001)")
    message: str = Field(..., description="Message lisible en français")
    details: Optional[Any] = Field(default=None, description="Détails techniques additionnels")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Horodatage ISO 8601")
    request_id: str = Field(..., description="Identifiant unique pour la traçabilité")


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PaginationMetadata(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    total_count: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationMetadata
