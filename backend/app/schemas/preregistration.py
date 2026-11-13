from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PreRegistrationCreate(BaseModel):
    formation_id: int
    consent_rgpd: bool = Field(..., description="Consentement explicite RGPD obligatoire")
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None


class PreRegistrationUpdate(BaseModel):
    formation_id: Optional[int] = None
    observations: Optional[str] = None


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="confirme, refuse, ajuste")
    observations: Optional[str] = Field(None, max_length=1000)
    nouvelle_formation_id: Optional[int] = Field(None, description="Requis si décision = ajuste")


class PreRegistrationResponse(BaseModel):
    id: int
    candidate_id: int
    formation_id: Optional[int]
    date_demande: datetime
    decision: str
    observations: Optional[str]

    class Config:
        from_attributes = True
