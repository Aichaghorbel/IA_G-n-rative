"""
Schémas Pydantic pour les RendezVous et Entretiens.
Strictement conformes au diagramme de classes UML.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AppointmentSlotResponse(BaseModel):
    """Créneau disponible exposé par l'API."""
    id: str
    enseignant_id: int
    enseignant_nom: str
    date_creneau: datetime
    disponible: bool = True


class AppointmentCreate(BaseModel):
    """Schéma de création d'un RendezVous."""
    date_proposee: datetime
    lieu: Optional[str] = "en ligne"


class AppointmentUpdate(BaseModel):
    """Schéma de mise à jour d'un RendezVous."""
    date_proposee: Optional[datetime] = None
    status: Optional[str] = None
    lieu: Optional[str] = None


class AppointmentOutcomeRequest(BaseModel):
    """Schéma de saisie du résultat d'entretien par l'enseignant."""
    decision_finale: str = Field(..., description="Favorable, Défavorable")
    observations: str = Field(..., max_length=2000, description="Observations et compte-rendu de l'entretien")


class AppointmentResponse(BaseModel):
    """Schéma de réponse pour un RendezVous."""
    id: int
    candidat_id: int
    enseignant_id: Optional[int] = None
    dateHeure: Optional[datetime] = None
    statut: str
    salleOuLien: Optional[str] = None

    class Config:
        from_attributes = True
