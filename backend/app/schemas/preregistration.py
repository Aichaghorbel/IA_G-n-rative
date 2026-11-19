"""
Schémas Pydantic pour les Préinscriptions.
Strictement conformes au diagramme de classes UML.

Preinscription: candidat_id, formation_id, dateCreation, statut
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PreRegistrationCreate(BaseModel):
    """Schéma de création d'une Préinscription."""
    formation_id: int
    consent_rgpd: bool = Field(..., description="Consentement explicite RGPD obligatoire")
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None


class PreRegistrationUpdate(BaseModel):
    """Schéma de mise à jour d'une Préinscription."""
    formation_id: Optional[int] = None
    statut: Optional[str] = None


class DecisionRequest(BaseModel):
    """Schéma de décision sur une Préinscription."""
    statut: str = Field(..., description="accepté, refusé")
    nouvelle_formation_id: Optional[int] = Field(None, description="Requis si ajustement de formation")


class PreRegistrationResponse(BaseModel):
    """Schéma de réponse pour une Préinscription."""
    id: int
    candidat_id: int
    formation_id: int
    dateCreation: Optional[date] = None
    statut: str

    class Config:
        from_attributes = True
