from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AppointmentSlotResponse(BaseModel):
    id: str
    enseignant_id: int
    enseignant_nom: str
    date_creneau: datetime
    disponible: bool = True


class AppointmentCreate(BaseModel):
    preinscription_id: int
    date_proposee: datetime
    lieu: Optional[str] = "en ligne"


class AppointmentUpdate(BaseModel):
    date_proposee: Optional[datetime] = None
    date_confirmee: Optional[datetime] = None
    status: Optional[str] = None
    lieu: Optional[str] = None


class AppointmentOutcomeRequest(BaseModel):
    decision_finale: str = Field(..., description="admis, refuse, en_attente, complement_demande")
    observations: str = Field(..., max_length=2000, description="Observations et compte-rendu de l'entretien")


class AppointmentResponse(BaseModel):
    id: int
    preinscription_id: Optional[int] = None
    candidat_id: int
    enseignant_id: Optional[int] = None
    date_proposee: Optional[datetime] = None
    date_confirmee: Optional[datetime] = None
    status: str
    lieu: str
    observations: Optional[str] = None
    decision_finale: str
    created_at: datetime

    class Config:
        from_attributes = True
