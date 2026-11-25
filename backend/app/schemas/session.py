from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SessionCreated(BaseModel):
    session_id: str
    session_token: str
    expires_at: datetime
    expires_in_seconds: int


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    message_count: int
    is_identified: bool


class SessionMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    created_at: datetime


class ProfileUpdate(BaseModel):
    niveau: Optional[str] = Field(None, max_length=200)
    interets: Optional[List[str]] = None
    matieres_preferees: Optional[List[str]] = None
    objectif_professionnel: Optional[str] = Field(None, max_length=200)
    formation_envisagee: Optional[str] = Field(None, max_length=200)
    langue: Optional[str] = Field(None, max_length=20)


class SessionProfile(BaseModel):
    profile: Dict[str, Any]