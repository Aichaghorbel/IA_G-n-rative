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


# ------------------------------------------------------------------ SA-29 : liaison session -> candidat
class LinkedConversationPreview(BaseModel):
    conversation_id: int
    titre: Optional[str] = None
    message_count: int = 0
    first_message: Optional[str] = None
    last_activity: Optional[datetime] = None


class SessionLinkProposal(BaseModel):
    """Proposition faite au candidat juste après son identification."""
    available: bool
    already_linked: bool = False
    reason: Optional[str] = None
    session_id: str
    conversations_count: int = 0
    messages_count: int = 0
    has_profile_data: bool = False
    conversations: List[LinkedConversationPreview] = []
    consent_required: bool = True
    consent_message: str = (
        "Souhaitez-vous associer votre conversation précédente à votre profil candidat ? "
        "Elle sera alors rattachée à votre compte et ne sera plus accessible comme visiteur anonyme."
    )


class SessionLinkRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64,
                            description="Identifiant de la session visiteur (renvoyé par la proposition)")
    consent: bool = Field(..., description="Doit être true : accord explicite du candidat")


class SessionLinkResult(BaseModel):
    linked: bool
    already_linked: bool = False
    candidate_id: int
    session_id: str
    conversations_linked: int = 0
    messages_linked: int = 0
    message: str
