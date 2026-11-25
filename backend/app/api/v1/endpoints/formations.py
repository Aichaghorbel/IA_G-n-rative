from datetime import date
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_db, require_roles, get_current_principal, VisitorSession
from app.core.rbac import Role
from app.core.exceptions import ResourceNotFoundException
from app.models.user import User
from app.models.formation import Formation, Tarif, Equivalence, Specialite, ProgrammeEtude, Matiere


# ==============================================================================
# 1. Pydantic Schemas - DTOs de Lecture & Validation Entrées (CRUD)
# ==============================================================================

# --- Matières ---
class MatiereDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str] = None
    coefficient: int = 1
    volumeHoraire: int = 42


class MatiereCreate(BaseModel):
    nom: str = Field(..., min_length=2, description="Nom obligatoire de la matière")
    description: Optional[str] = None
    coefficient: int = Field(1, ge=1, description="Coefficient de pondération")
    volumeHoraire: int = Field(42, ge=1, description="Nombre total d'heures")


class MatiereUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    coefficient: Optional[int] = Field(None, ge=1)
    volumeHoraire: Optional[int] = Field(None, ge=1)


# --- Programmes d'Études (Semestres) ---
class ProgrammeEtudeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str] = None
    semestre: int = 1
    matieres: List[MatiereDTO] = []


class ProgrammeEtudeCreate(BaseModel):
    nom: str = Field(..., min_length=2, description="Intitulé obligatoire du programme")
    description: Optional[str] = None
    semestre: int = Field(1, ge=1, le=10, description="Numéro de semestre")


class ProgrammeEtudeUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    semestre: Optional[int] = Field(None, ge=1, le=10)


# --- Spécialités ---
class SpecialiteDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str] = None
    programmes: List[ProgrammeEtudeDTO] = []


class SpecialiteCreate(BaseModel):
    nom: str = Field(..., min_length=2, description="Intitulé de la spécialité")
    description: Optional[str] = None


class SpecialiteUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None


# --- Tarifs & Frais de Scolarité ---
class TarifDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    montant_9mois: float
    type: str
    Annee: Optional[str] = None
    annee: Optional[str] = None
    devise: str
    modalites_paiement: Optional[str] = None


class TarifCreate(BaseModel):
    montant_9mois: float = Field(..., ge=0, description="Montant des frais de scolarité")
    type: str = Field(..., description="Type de tarif : 'fraisNational' ou 'frais international'")
    Annee: str = Field(..., description="Année universitaire, ex: '2026-2027'")
    devise: str = Field("DT", description="Monnaie : 'DT' ou '€'")
    modalites_paiement: Optional[str] = Field(None, description="Modalités de paiement (ex: 3 tranches)")


class TarifUpdate(BaseModel):
    montant_9mois: Optional[float] = Field(None, ge=0)
    type: Optional[str] = None
    Annee: Optional[str] = None
    devise: Optional[str] = None
    modalites_paiement: Optional[str] = None


# --- Équivalences ---
class EquivalenceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    desciption: Optional[str] = None
    conditions: Optional[str] = None
    formation_Origine: str


# --- Formations (Lecture, Création, Modification) ---
class FormationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    universite: str
    description: str
    objectif: Optional[str] = None
    duree: int = 3
    debouches: Optional[str] = None
    conditionsAdmission: Optional[str] = None
    prerequis: Optional[str] = None
    statut_publication: str = "publie"
    date_debut_validite: Optional[date] = None
    date_fin_validite: Optional[date] = None
    tarifs: List[TarifDTO] = []
    equivalences: List[EquivalenceDTO] = []
    specialites: List[SpecialiteDTO] = []


class FormationCreate(BaseModel):
    nom: str = Field(..., min_length=3, description="Nom officiel de la formation (obligatoire)")
    universite: str = Field(..., description="Établissement : 'IIT' ou 'ISB' (obligatoire)")
    description: str = Field(..., min_length=10, description="Description générale (obligatoire)")
    objectif: Optional[str] = None
    duree: int = Field(3, ge=1, le=7, description="Durée en années (ex: 3 pour Licence, 5 pour Ingénieur)")
    debouches: Optional[str] = None
    conditionsAdmission: Optional[str] = Field(None, description="Conditions et critères d'admission officiels")
    prerequis: Optional[str] = None
    statut_publication: str = Field("publie", description="'publie', 'brouillon' ou 'archive'")
    date_debut_validite: Optional[date] = None
    date_fin_validite: Optional[date] = None


class FormationUpdate(BaseModel):
    nom: Optional[str] = None
    universite: Optional[str] = None
    description: Optional[str] = None
    objectif: Optional[str] = None
    duree: Optional[int] = Field(None, ge=1, le=7)
    debouches: Optional[str] = None
    conditionsAdmission: Optional[str] = None
    prerequis: Optional[str] = None
    statut_publication: Optional[str] = None
    date_debut_validite: Optional[date] = None
    date_fin_validite: Optional[date] = None


router = APIRouter()


# ==============================================================================
# 2. Endpoints Formations : Consultation, Recherche et Filtrage Avancés
# ==============================================================================
@router.get(
    "/",
    response_model=List[FormationResponse],
    summary="Catalogue et Recherche Avancée des Formations (IIT / ISB)",
    description="Permet de rechercher par mot-clé, filtrer par université, statut de publication ou durée."
)
def list_formations(
    q: Optional[str] = Query(None, description="Recherche textuelle libre (nom, description, conditions)"),
    universite: Optional[str] = Query(None, description="Filtre par université (IIT, ISB)"),
    duree: Optional[int] = Query(None, description="Filtre par durée d'études en années (ex: 3, 5)"),
    statut: Optional[str] = Query(None, description="Filtre par statut (publie, brouillon, archive)"),
    db: Session = Depends(get_db),
    principal: Union[User, VisitorSession] = Depends(get_current_principal)
):
    query = db.query(Formation)
    is_admin = Role.normalize(principal.role) == Role.ADMINISTRATEUR

    # Règle Métier : Les Candidats, Visiteurs et l'Agent IA ne consultent
    # QUE les formations officielles publiées et dont la période est valide
    if not is_admin:
        today = date.today()
        query = query.filter(Formation.statut_publication == "publie")
        query = query.filter(
            or_(Formation.date_debut_validite.is_(None), Formation.date_debut_validite <= today)
        )
        query = query.filter(
            or_(Formation.date_fin_validite.is_(None), Formation.date_fin_validite >= today)
        )
    else:
        # L'administrateur/responsable peut filtrer par n'importe quel statut
        if statut:
            query = query.filter(Formation.statut_publication.ilike(statut))

    # Filtrage par université
    if universite:
        query = query.filter(Formation.universite.ilike(f"%{universite}%"))

    # Filtrage par durée
    if duree:
        query = query.filter(Formation.duree == duree)

    # Recherche plein texte par mot-clé
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Formation.nom.ilike(term),
                Formation.description.ilike(term),
                Formation.conditionsAdmission.ilike(term),
                Formation.debouches.ilike(term)
            )
        )

    return query.all()


@router.get(
    "/{formation_id}",
    response_model=FormationResponse,
    summary="Détail d'une Formation avec Spécialités, Matières et Tarifs"
)
def get_formation_detail(
    formation_id: int,
    db: Session = Depends(get_db),
    principal: Union[User, VisitorSession] = Depends(get_current_principal)
):
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", formation_id)

    # Règle Métier : Candidats et IA ne peuvent pas consulter les brouillons ou formations expirées
    is_admin = Role.normalize(principal.role) == Role.ADMINISTRATEUR
    if not is_admin:
        today = date.today()
        if formation.statut_publication != "publie":
            raise ResourceNotFoundException("formation", formation_id)
        if formation.date_debut_validite and formation.date_debut_validite > today:
            raise ResourceNotFoundException("formation", formation_id)
        if formation.date_fin_validite and formation.date_fin_validite < today:
            raise ResourceNotFoundException("formation", formation_id)

    return formation


# ==============================================================================
# 3. Endpoints Formations : CRUD Responsable / Administrateur
# ==============================================================================
@router.post(
    "/",
    response_model=FormationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle Formation (Responsable / Admin uniquement)",
    description="Permet d'ajouter une formation avec ses conditions d'admission, durée, et période de validité."
)
def create_formation(
    formation_in: FormationCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    formation = Formation(**formation_in.model_dump())
    db.add(formation)
    db.commit()
    db.refresh(formation)
    return formation


@router.put(
    "/{formation_id}",
    response_model=FormationResponse,
    summary="Modifier une Formation existante (Responsable / Admin uniquement)"
)
def update_formation(
    formation_id: int,
    formation_in: FormationUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", formation_id)

    update_data = formation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(formation, field, value)

    db.commit()
    db.refresh(formation)
    return formation


@router.delete(
    "/{formation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une Formation (Responsable / Admin uniquement)"
)
def delete_formation(
    formation_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", formation_id)

    db.delete(formation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# 4. Endpoints Tarifs & Modalités de Paiement (Frais de scolarité)
# ==============================================================================
@router.post(
    "/{formation_id}/tarifs",
    response_model=TarifDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un Tarif / Frais de scolarité (Responsable / Admin uniquement)"
)
def create_tarif(
    formation_id: int,
    tarif_in: TarifCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", formation_id)

    tarif = Tarif(
        formation_id=formation_id,
        montant_9mois=tarif_in.montant_9mois,
        type=tarif_in.type,
        Annee=tarif_in.Annee,
        devise=tarif_in.devise,
        modalites_paiement=tarif_in.modalites_paiement
    )
    db.add(tarif)
    db.commit()
    db.refresh(tarif)
    return tarif


@router.put(
    "/tarifs/{tarif_id}",
    response_model=TarifDTO,
    summary="Modifier un Tarif / Modalités de paiement (Responsable / Admin uniquement)"
)
def update_tarif(
    tarif_id: int,
    tarif_in: TarifUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    tarif = db.query(Tarif).filter(Tarif.id == tarif_id).first()
    if not tarif:
        raise ResourceNotFoundException("tarif", tarif_id)

    update_data = tarif_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "Annee":
            tarif.Annee = value
        elif field == "montant_9mois":
            tarif.montant_9mois = value
        else:
            setattr(tarif, field, value)

    db.commit()
    db.refresh(tarif)
    return tarif


@router.delete(
    "/tarifs/{tarif_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un Tarif (Responsable / Admin uniquement)"
)
def delete_tarif(
    tarif_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    tarif = db.query(Tarif).filter(Tarif.id == tarif_id).first()
    if not tarif:
        raise ResourceNotFoundException("tarif", tarif_id)

    db.delete(tarif)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# 5. Endpoints Spécialités
# ==============================================================================
@router.post(
    "/{formation_id}/specialites",
    response_model=SpecialiteDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une Spécialité à une Formation (Responsable / Admin uniquement)"
)
def create_specialite(
    formation_id: int,
    specialite_in: SpecialiteCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    formation = db.query(Formation).filter(Formation.id == formation_id).first()
    if not formation:
        raise ResourceNotFoundException("formation", formation_id)

    specialite = Specialite(
        formation_id=formation_id,
        nom=specialite_in.nom,
        description=specialite_in.description
    )
    db.add(specialite)
    db.commit()
    db.refresh(specialite)
    return specialite


@router.put(
    "/specialites/{specialite_id}",
    response_model=SpecialiteDTO,
    summary="Modifier une Spécialité (Responsable / Admin uniquement)"
)
def update_specialite(
    specialite_id: int,
    specialite_in: SpecialiteUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    specialite = db.query(Specialite).filter(Specialite.id == specialite_id).first()
    if not specialite:
        raise ResourceNotFoundException("specialite", specialite_id)

    update_data = specialite_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(specialite, field, value)

    db.commit()
    db.refresh(specialite)
    return specialite


@router.delete(
    "/specialites/{specialite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une Spécialité (Responsable / Admin uniquement)"
)
def delete_specialite(
    specialite_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    specialite = db.query(Specialite).filter(Specialite.id == specialite_id).first()
    if not specialite:
        raise ResourceNotFoundException("specialite", specialite_id)

    db.delete(specialite)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# 6. Endpoints Programmes Pédagogiques (Semestres)
# ==============================================================================
@router.post(
    "/specialites/{specialite_id}/programmes",
    response_model=ProgrammeEtudeDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un Programme Pédagogique à une Spécialité (Responsable / Admin uniquement)"
)
def create_programme(
    specialite_id: int,
    programme_in: ProgrammeEtudeCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    specialite = db.query(Specialite).filter(Specialite.id == specialite_id).first()
    if not specialite:
        raise ResourceNotFoundException("specialite", specialite_id)

    programme = ProgrammeEtude(
        specialite_id=specialite_id,
        nom=programme_in.nom,
        description=programme_in.description,
        semestre=programme_in.semestre
    )
    db.add(programme)
    db.commit()
    db.refresh(programme)
    return programme


@router.put(
    "/programmes/{programme_id}",
    response_model=ProgrammeEtudeDTO,
    summary="Modifier un Programme Pédagogique (Responsable / Admin uniquement)"
)
def update_programme(
    programme_id: int,
    programme_in: ProgrammeEtudeUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    programme = db.query(ProgrammeEtude).filter(ProgrammeEtude.id == programme_id).first()
    if not programme:
        raise ResourceNotFoundException("programme", programme_id)

    update_data = programme_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(programme, field, value)

    db.commit()
    db.refresh(programme)
    return programme


@router.delete(
    "/programmes/{programme_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un Programme Pédagogique (Responsable / Admin uniquement)"
)
def delete_programme(
    programme_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    programme = db.query(ProgrammeEtude).filter(ProgrammeEtude.id == programme_id).first()
    if not programme:
        raise ResourceNotFoundException("programme", programme_id)

    db.delete(programme)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# 7. Endpoints Matières (Cours, Coefficients, Volumes horaires)
# ==============================================================================
@router.post(
    "/programmes/{programme_id}/matieres",
    response_model=MatiereDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une Matière à un Programme Pédagogique (Responsable / Admin uniquement)"
)
def create_matiere(
    programme_id: int,
    matiere_in: MatiereCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    programme = db.query(ProgrammeEtude).filter(ProgrammeEtude.id == programme_id).first()
    if not programme:
        raise ResourceNotFoundException("programme", programme_id)

    matiere = Matiere(
        programme_id=programme_id,
        nom=matiere_in.nom,
        description=matiere_in.description,
        coefficient=matiere_in.coefficient,
        volumeHoraire=matiere_in.volumeHoraire
    )
    db.add(matiere)
    db.commit()
    db.refresh(matiere)
    return matiere


@router.put(
    "/matieres/{matiere_id}",
    response_model=MatiereDTO,
    summary="Modifier une Matière (Responsable / Admin uniquement)"
)
def update_matiere(
    matiere_id: int,
    matiere_in: MatiereUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()
    if not matiere:
        raise ResourceNotFoundException("matiere", matiere_id)

    update_data = matiere_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(matiere, field, value)

    db.commit()
    db.refresh(matiere)
    return matiere


@router.delete(
    "/matieres/{matiere_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une Matière (Responsable / Admin uniquement)"
)
def delete_matiere(
    matiere_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("Responsable", "Administrateur"))
):
    matiere = db.query(Matiere).filter(Matiere.id == matiere_id).first()
    if not matiere:
        raise ResourceNotFoundException("matiere", matiere_id)

    db.delete(matiere)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
