from typing import Dict, List
from pydantic import BaseModel


class OverviewStatsResponse(BaseModel):
    conversations: int
    orientations: int
    preinscriptions: int
    entretiens: int
    inscriptions: int


class ProgramDemandItem(BaseModel):
    formation_nom: str
    etablissement: str
    candidatures_count: int
    score_moyen: float


class ProgramsStatsResponse(BaseModel):
    total_iit: int
    total_isb: int
    top_formations: List[ProgramDemandItem]


class FunnelStep(BaseModel):
    step: str
    count: int
    conversion_rate: float


class FunnelStatsResponse(BaseModel):
    steps: List[FunnelStep]
    taux_global_conversion: float


class QCMStatItem(BaseModel):
    formation_nom: str
    moyenne_score: float
    nb_evaluations: int


class QCMStatsResponse(BaseModel):
    statistiques: List[QCMStatItem]
