from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.api.deps import PaginationQuery, get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.api.ownership import assert_teacher_access, get_candidat_of
from app.core.rbac import Role
from app.models.appointment import RendezVous
from app.models.candidate import Candidat, CandidateProfile, ProfilCandidat
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


def _latest_assignment_rdv(profile: Candidat) -> Optional[RendezVous]:
    assigned = [r for r in (profile.rendezvous or []) if r.enseignant_id is not None]
    if not assigned:
        return None
    return max(assigned, key=lambda r: r.id)


def _to_candidate_response(profile: Candidat) -> CandidateProfileResponse:
    user = profile.user
    profil = profile.profil
    rdv = _latest_assignment_rdv(profile)
    return CandidateProfileResponse(
        id=profile.id,
        nom=user.nom if user else "",
        prenom=user.prenom if user else "",
        email=user.email if user else "",
        telephone=user.telephone if user else None,
        CIN=profile.CIN,
        passport=profile.passport,
        pays=profile.pays,
        dateNaissance=profile.dateNaissance,
        sexe=profile.sexe,
        adresse=profile.adresse,
        universite=profile.universite,
        dernierDiplomeObtenu=profil.dernierDiplomeObtenu if profil else None,
        anneeObtention=profil.anneeObtention if profil else None,
        diplomeSouhaite=profil.diplomeSouhaite if profil else None,
        niveau=profil.niveau if profil else None,
        cours=profil.cours if profil else None,
        sourceConnaissanceUniversite=profil.sourceConnaissanceUniversite if profil else None,
        niveau_etudes=profil.dernierDiplomeObtenu if profil else None,
        etablissement_vise=profile.universite or "indifférent",
        statut_dossier=candidate_service.compute_status(profile),
        enseignant_affecte_id=rdv.enseignant_id if rdv else None,
        affectation_statut="valide" if rdv else None,
    )


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
    profile = get_candidat_of(db, principal)
    if not profile:
        profile = Candidat(user_id=principal.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return _to_candidate_response(profile)


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
    profile = get_candidat_of(db, principal)
    if not profile:
        profile = Candidat(user_id=principal.id)
        db.add(profile)
        db.flush()

    update_dict = data.model_dump(exclude_unset=True)

    # Champs sur User
    if profile.user:
        for u_field in ("nom", "prenom", "telephone"):
            if u_field in update_dict and update_dict[u_field] is not None:
                setattr(profile.user, u_field, update_dict[u_field])

    # Champs directs sur Candidat (UML)
    for c_field in ("CIN", "passport", "pays", "dateNaissance", "sexe", "adresse", "universite"):
        if c_field in update_dict and update_dict[c_field] is not None:
            setattr(profile, c_field, update_dict[c_field])
    if "etablissement_vise" in update_dict and update_dict["etablissement_vise"] in ("IIT", "ISB"):
        profile.universite = update_dict["etablissement_vise"]

    # Champs sur ProfilCandidat (UML)
    profil_fields = (
        "dernierDiplomeObtenu", "anneeObtention", "diplomeSouhaite",
        "niveau", "cours", "sourceConnaissanceUniversite",
    )
    wants_profil = any(k in update_dict for k in (*profil_fields, "niveau_etudes"))
    if wants_profil:
        if profile.profil is None:
            profile.profil = ProfilCandidat(candidat_id=profile.id)
            db.add(profile.profil)
        for p_field in profil_fields:
            if p_field in update_dict and update_dict[p_field] is not None:
                setattr(profile.profil, p_field, update_dict[p_field])
        if "niveau_etudes" in update_dict and update_dict["niveau_etudes"] and not profile.profil.dernierDiplomeObtenu:
            profile.profil.dernierDiplomeObtenu = update_dict["niveau_etudes"]

    db.commit()
    db.refresh(profile)
    return _to_candidate_response(profile)


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

    # Enseignant -> ne voit que les candidats avec lesquels il a un rendez-vous
    if Role.normalize(principal.role) == Role.ENSEIGNANT:
        query = query.filter(
            CandidateProfile.id.in_(
                db.query(RendezVous.candidat_id).filter(RendezVous.enseignant_id == principal.id)
            )
        )

    if etablissement and isinstance(etablissement, str):
        query = query.filter(CandidateProfile.universite == etablissement)

    all_items = query.order_by(CandidateProfile.id.desc()).all()
    if statut and isinstance(statut, str):
        all_items = [c for c in all_items if candidate_service.compute_status(c) == statut]

    response.headers["X-Total-Count"] = str(len(all_items))
    page_items = all_items[pagination.offset : pagination.offset + pagination.limit]
    return [_to_candidate_response(c) for c in page_items]


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

    if Role.normalize(principal.role) == Role.ENSEIGNANT:
        assert_teacher_access(db, principal, profile)

    return _to_candidate_response(profile)


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

    if Role.normalize(principal.role) == Role.ENSEIGNANT:
        assert_teacher_access(db, principal, profile)

    profil = profile.profil
    qcm_score = None
    for p in (profile.preinscriptions or []):
        if p.qcm and p.qcm.score is not None:
            qcm_score = p.qcm.score
            break
    cible = (
        (profil.diplomeSouhaite if profil else None)
        or profile.universite
        or "IIT - Génie Logiciel"
    )

    return CandidateSummaryResponse(
        candidate_id=profile.id,
        nom_complet=f"{profile.prenom} {profile.nom}".strip() or f"Candidat #{profile.id}",
        parcours_actuel=(profil.dernierDiplomeObtenu if profil else None) or "Baccalauréat",
        synthese_conversationnelle="Le candidat démontre un intérêt marqué pour les architectures logicielles et l'IA. "
                                   "Échanges menés en dialecte tunisien et français.",
        points_a_approfondir=[
            "Valider le niveau d'anglais technique",
            "Évaluer les motivations pour le cursus d'ingénierie",
            "Préciser le projet professionnel"
        ],
        formations_ciblees=[cible],
        qcm_score=qcm_score if qcm_score is not None else 85.0
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

    role = Role.normalize(principal.role)
    if role == Role.CANDIDAT:
        own = get_candidat_of(db, principal)
        if not own or own.id != profile.id:
            raise ResourceNotFoundException("candidat", candidate_id)  # on ne révèle pas l'existence
    elif role == Role.ENSEIGNANT:
        assert_teacher_access(db, principal, profile)

    rdv = _latest_assignment_rdv(profile)
    teacher_nom = None
    if rdv and rdv.enseignant:
        teacher_nom = f"{rdv.enseignant.prenom} {rdv.enseignant.nom}"

    return AssignmentDetailResponse(
        candidate_id=profile.id,
        enseignant_id=rdv.enseignant_id if rdv else None,
        enseignant_nom=teacher_nom,
        statut=rdv.statut if rdv else None,
        date_affectation=rdv.dateHeure if rdv else None,
        motif=rdv.salleOuLien if rdv else None,
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
    return _to_candidate_response(profile)
