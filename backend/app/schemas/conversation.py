from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageSource(BaseModel):
    document_id: int
    title: str
    page: Optional[int] = None
    url: Optional[str] = None


class MessageCreate(BaseModel):
    message: str = Field(..., max_length=5000, description="Message du candidat en français, tunisien ou Arabizi")


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    audio_url: Optional[str] = None
    language_detected: Optional[str] = "fr"
    sources: List[MessageSource] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message_id: int
    response: str
    language_detected: str
    intent_detected: str
    sources: List[MessageSource] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime


class ConversationResponse(BaseModel):
    conversation_id: int
    session_id: Optional[str] = None
    is_anonymous: bool = True
    language_detected: str = "fr"
    intent_detected: str = "info_programme"
    messages: List[MessageItem] = []
    memory_summary: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class AudioPreferenceRequest(BaseModel):
    audio_enabled: bool = Field(..., description="Active ou désactive la réponse vocale")
