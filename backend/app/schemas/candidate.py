from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class CandidateProfileUpdate(BaseModel):
    nom: Optional[str] = Field(None, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    telephone: Optional[str] = None
    niveau_etudes: Optional[str] = Field(None, description="lycéen, bac, bac+1, bac+2, bac+3, équivalence")
    etablissement_origine: Optional[str] = Field(None, max_length=200)
    specialites: Optional[List[str]] = Field(default=None, max_length=5)
    interets: Optional[List[str]] = Field(default=None, max_length=10)
    matieres_preferees: Optional[List[str]] = Field(default=None, max_length=5)
    objectif_professionnel: Optional[str] = Field(None, max_length=500)
    contraintes: Optional[str] = Field(None, max_length=500)
    etablissement_vise: Optional[str] = Field(None, description="IIT, ISB, indifférent")


class CandidateProfileResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    telephone: Optional[str] = None
    niveau_etudes: Optional[str] = None
    etablissement_origine: Optional[str] = None
    specialites: List[str] = []
    interets: List[str] = []
    matieres_preferees: List[str] = []
    objectif_professionnel: Optional[str] = None
    contraintes: Optional[str] = None
    etablissement_vise: str = "indifférent"
    statut_dossier: str
    enseignant_affecte_id: Optional[int] = None
    affectation_statut: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateSummaryResponse(BaseModel):
    candidate_id: int
    nom_complet: str
    parcours_actuel: str
    synthese_conversationnelle: str
    points_a_approfondir: List[str]
    formations_ciblees: List[str]
    qcm_score: Optional[float] = None


class AutoAssignResponse(BaseModel):
    candidate_id: int
    enseignant_propose_id: int
    enseignant_nom: str
    statut: str = "auto_proposed"
    score_affinite: float
    motif: str


class AssignRequest(BaseModel):
    enseignant_id: int
    motif: Optional[str] = Field(None, description="Motif de validation ou de modification")


class AssignmentDetailResponse(BaseModel):
    candidate_id: int
    enseignant_id: Optional[int]
    enseignant_nom: Optional[str]
    statut: Optional[str]
    date_affectation: Optional[datetime]
    motif: Optional[str]
