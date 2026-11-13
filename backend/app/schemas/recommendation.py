from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ParcoursItem(BaseModel):
    formation_id: int
    formation_nom: str
    score_compatibilite: float = Field(..., ge=0.0, le=1.0)
    justification: str
    avantages: List[str] = []
    prerequis: List[str] = []
    debouches: List[str] = []


class RecommendationResponse(BaseModel):
    id: int
    candidat_id: int
    parcours: List[ParcoursItem]
    status: str  # genere, valide, ajuste, refuse
    genere_par: str = "agent_ia"
    valide_par: Optional[int] = None
    motif_rejet: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationRejectRequest(BaseModel):
    motif: str = Field(..., max_length=500, description="Motif du refus pour affiner la nouvelle génération")


class RecommendationAdjustRequest(BaseModel):
    nouvelle_formation_id: int
    justification: str = Field(..., max_length=1000)
