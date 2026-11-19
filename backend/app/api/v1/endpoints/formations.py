from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.models.formation import Formation, Tarif, Equivalence, Specialite, ProgrammeEtude, Matiere
from app.models.enums import Universite
from pydantic import BaseModel, ConfigDict


# ==============================================================================
# Pydantic Schemas for Formations & Curriculum Catalog (Class Diagram)
# ==============================================================================
class MatiereDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str] = None
    coefficient: int = 1
    volumeHoraire: int = 42


class ProgrammeEtudeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str] = None
    semestre: int = 1
    matieres: List[MatiereDTO] = []


class SpecialiteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str] = None
    programmes: List[ProgrammeEtudeDTO] = []


class TarifDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    montant_9mois: float
    type: str
    Annee: Optional[str] = None
    annee: Optional[str] = None
    devise: str


class EquivalenceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    desciption: Optional[str] = None
    conditions: Optional[str] = None
    formation_Origine: str


class FormationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    universite: str
    description: str
    objectif: Optional[str] = None
    duree: int = 3
    debouches: Optional[object] = None
    conditionsAdmission: Optional[str] = None
    prerequis: Optional[object] = None
    tarifs: List[TarifDTO] = []
    equivalences: List[EquivalenceDTO] = []
    specialites: List[SpecialiteDTO] = []


router = APIRouter()


@router.get(
    "/",
    response_model=List[FormationResponse],
    summary="Catalogue des Formations & Programmes (IIT / ISB)",
    description="Retourne la liste complète des formations avec leurs tarifs, équivalences et arborescence de spécialités."
)
def list_formations(
    universite: Optional[str] = Query(None, description="Filtre par université (IIT, ISB)"),
    db: Session = Depends(get_db)
):
    """
    Explore le catalogue académique conforme au diagramme de classes SmartCampus.
    Accessible publiquement (Visiteurs, Candidats, Enseignants, Administrateurs).
    """
    query = db.query(Formation)
    if universite:
        query = query.filter(Formation.universite.ilike(f"%{universite}%"))
    return query.all()


@router.get(
    "/{formation_id}",
    response_model=FormationResponse,
    summary="Détail d'une Formation avec Spécialités et Matières",
    description="Retourne le cursus complet : Spécialités, Programmes d'études, Semestres, Matières avec coefficients et volumes horaires."
)
def get_formation_detail(
    formation_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une formation complète par son identifiant unique.
    """
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", formation_id)
    return formation
