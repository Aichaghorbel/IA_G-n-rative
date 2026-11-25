"""
Schémas Pydantic pour les Recommandations d'orientation.
Strictement conformes au diagramme de classes UML.
Recommandation est liée uniquement au Candidat (pas de formation_id).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RecommandationCreate(BaseModel):
    """Schéma de création d'une Recommandation."""
    candidat_id: int
    nom: Optional[str] = None
    scoreComptabilite: float = Field(0.0, ge=0.0, le=1.0)
    justification: str
    statut: Optional[str] = "à validée"


class RecommandationUpdate(BaseModel):
    """Schéma de mise à jour d'une Recommandation."""
    nom: Optional[str] = None
    scoreComptabilite: Optional[float] = Field(None, ge=0.0, le=1.0)
    justification: Optional[str] = None
    statut: Optional[str] = None


class RecommandationResponse(BaseModel):
    """Schéma de réponse pour une Recommandation."""
    id: int
    candidat_id: int
    nom: Optional[str] = None
    scoreComptabilite: float
    justification: str
    statut: str
    dateGeneration: Optional[datetime] = None

    class Config:
        from_attributes = True


# Alias de compatibilité
RecommendationResponse = RecommandationResponse
RecommendationRejectRequest = RecommandationUpdate
RecommendationAdjustRequest = RecommandationUpdate
