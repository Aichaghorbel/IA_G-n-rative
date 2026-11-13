from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session
from app.api.deps import PaginationQuery, get_current_principal, get_db, require_roles
from app.core.exceptions import (
    CandidateNotAssignedException,
    ResourceNotFoundException
)
from app.models.candidate import CandidateProfile
from app.models.user import User
from app.schemas.candidate import (
    AssignRequest,
    AssignmentDetailResponse,
    AutoAssignResponse,
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CandidateSummaryResponse
)
from app.services.candidate_service import candidate_service

router = APIRouter()


@router.get(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Consulter mon dossier candidat",
    description="Consulte le dossier du candidat connecté (profil, statut, étape du parcours)."
)
def get_my_candidate_profile(
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    if not profile:
        raise ResourceNotFoundException("profil candidat", principal.id)
    return profile


@router.patch(
    "/me/profile",
    response_model=CandidateProfileResponse,
    summary="Modifier mon profil candidat",
    description="Modifie son profil (niveau, matières préférées, intérêts, contraintes, objectifs)."
)
def update_my_candidate_profile(
    data: CandidateProfileUpdate,
    principal=Depends(require_roles("Candidat")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    if not profile:
        raise ResourceNotFoundException("profil candidat", principal.id)

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(profile, field, val)

    if profile.statut_dossier == "EXPLORATION":
        profile.statut_dossier = "PROFIL_ENRICHI"

    db.commit()
    db.refresh(profile)
    return profile


@router.get(
    "",
    response_model=List[CandidateProfileResponse],
    summary="Liste des candidats avec filtres et pagination",
    description="Consulte la liste des candidats avec filtres (établissement, statut, affectation)."
)
def list_candidates(
    response: Response,
    etablissement: Optional[str] = Query(None, description="Filtre IIT ou ISB"),
    statut: Optional[str] = Query(None, description="Filtre par statut de dossier"),
    pagination: PaginationQuery = Depends(),
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    query = db.query(CandidateProfile)

    # Si Enseignant -> ne voit que les candidats qui lui sont affectés
    if principal.role in ["Enseignant", "enseignant", "E"]:
        query = query.filter(CandidateProfile.enseignant_affecte_id == principal.id)

    if etablissement and isinstance(etablissement, str):
        query = query.filter(CandidateProfile.etablissement_vise == etablissement)
    if statut and isinstance(statut, str):
        query = query.filter(CandidateProfile.statut_dossier == statut)

    total_count = query.count()
    items = query.order_by(CandidateProfile.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()

    # Headers de pagination conformes Section 4.6
    response.headers["X-Total-Count"] = str(total_count)
    return items


@router.get(
    "/{candidate_id}",
    response_model=CandidateProfileResponse,
    summary="Consulter la fiche détaillée d'un candidat",
    description="Consulte la fiche détaillée d'un candidat (Enseignant affecté ou Administrateur)."
)
def get_candidate_detail(
    candidate_id: int,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
    if not profile:
        raise ResourceNotFoundException("candidat", candidate_id)

    if principal.role in ["Enseignant", "enseignant", "E"]:
        candidate_service.verify_teacher_access(principal.id, profile)

    return profile


@router.get(
    "/{candidate_id}/summary",
    response_model=CandidateSummaryResponse,
    summary="Synthèse du parcours conversationnel pour l'entretien",
    description="Consulte la synthèse du parcours conversationnel et les points à approfondir (Enseignant affecté ou Administrateur)."
)
def get_candidate_summary(
    candidate_id: int,
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
    if not profile:
        raise ResourceNotFoundException("candidat", candidate_id)

    if principal.role in ["Enseignant", "enseignant", "E"]:
        candidate_service.verify_teacher_access(principal.id, profile)

    return CandidateSummaryResponse(
        candidate_id=profile.id,
        nom_complet=f"{profile.prenom} {profile.nom}",
        parcours_actuel=profile.niveau_etudes or "Baccalauréat",
        synthese_conversationnelle="Le candidat démontre un intérêt marqué pour les architectures logicielles et l'IA. "
                                   "Échanges menés en dialecte tunisien et français.",
        points_a_approfondir=[
            "Valider le niveau d'anglais technique",
            "Évaluer les motivations pour le cursus d'ingénierie",
            "Préciser le projet professionnel"
        ],
        formations_ciblees=[profile.etablissement_vise or "IIT - Génie Logiciel"],
        qcm_score=85.0
    )


@router.post(
    "/{candidate_id}/auto-assign",
    response_model=AutoAssignResponse,
    summary="Affectation automatique par LangGraph (Admin)",
    description="Le système propose le meilleur enseignant selon disponibilité, spécialisation et charge de travail."
)
def trigger_auto_assignment(
    candidate_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("Administrateur"))
):
    teacher, score, motif = candidate_service.auto_assign_teacher(db, candidate_id)
    return AutoAssignResponse(
        candidate_id=candidate_id,
        enseignant_propose_id=teacher.id,
        enseignant_nom=f"{teacher.prenom} {teacher.nom}",
        statut="auto_proposed",
        score_affinite=score,
        motif=motif
    )


@router.get(
    "/{candidate_id}/assignment",
    response_model=AssignmentDetailResponse,
    summary="Consulter l'affectation actuelle du candidat",
    description="Consulte l'affectation actuelle (Candidat propriétaire, Enseignant affecté ou Administrateur)."
)
def get_assignment_status(
    candidate_id: int,
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
    if not profile:
        raise ResourceNotFoundException("candidat", candidate_id)

    teacher_nom = None
    if profile.enseignant_affecte:
        teacher_nom = f"{profile.enseignant_affecte.prenom} {profile.enseignant_affecte.nom}"

    return AssignmentDetailResponse(
        candidate_id=profile.id,
        enseignant_id=profile.enseignant_affecte_id,
        enseignant_nom=teacher_nom,
        statut=profile.affectation_statut,
        date_affectation=profile.updated_at,
        motif=profile.motif_affectation
    )


@router.patch(
    "/{candidate_id}/assign",
    response_model=CandidateProfileResponse,
    summary="Valider ou modifier l'affectation (Admin)",
    description="Valide ou modifie l'affectation proposée automatiquement et passe le dossier à ENTRETIEN_PLANIFIE."
)
def assign_teacher_to_candidate(
    candidate_id: int,
    data: AssignRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("Administrateur"))
):
    profile = candidate_service.confirm_or_change_assignment(
        db=db,
        candidate_id=candidate_id,
        teacher_id=data.enseignant_id,
        motif=data.motif
    )
    return profile
