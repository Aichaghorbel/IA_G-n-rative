from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_principal, get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.models.candidate import CandidateProfile
from app.models.qcm import QCM
from app.schemas.qcm import (
    QCMQuestionDTO,
    QCMResponse,
    QCMResultResponse,
    QCMSubmissionRequest
)
from app.services.candidate_service import candidate_service
from app.services.qcm_service import qcm_service

router = APIRouter()


@router.post(
    "",
    response_model=QCMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer un QCM ciblé",
    description="Génère un QCM adaptatif personnalisé selon le profil et la formation visée."
)
def generate_qcm(
    formation_id: Optional[int] = Query(None),
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    profile = None
    if principal.role in ["Candidat", "candidat", "C"]:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == principal.id).first()
    else:
        profile = db.query(CandidateProfile).filter(CandidateProfile.session_id == principal.session_id).first()

    candidate_id = profile.id if profile else 1
    qcm = qcm_service.generate_qcm(db, candidate_id=candidate_id, formation_id=formation_id)

    dto_questions = [
        QCMQuestionDTO(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            difficulty=q.difficulty
        )
        for q in qcm.questions
    ]

    return QCMResponse(
        id=qcm.id,
        candidate_id=qcm.candidate_id,
        formation_id=qcm.formation_id,
        total_questions=len(dto_questions),
        questions=dto_questions
    )


@router.get(
    "/{qcm_id}",
    response_model=QCMResponse,
    summary="Consulter les questions d'un QCM",
    description="Récupère les questions sans les réponses correctes pour éviter la triche (V/C)."
)
def get_qcm(
    qcm_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
    if not qcm:
        raise ResourceNotFoundException("QCM", qcm_id)

    dto_questions = [
        QCMQuestionDTO(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            difficulty=q.difficulty
        )
        for q in qcm.questions
    ]
    return QCMResponse(
        id=qcm.id,
        candidate_id=qcm.candidate_id,
        formation_id=qcm.formation_id,
        total_questions=len(dto_questions),
        questions=dto_questions
    )


@router.post(
    "/{qcm_id}/answers",
    response_model=QCMResultResponse,
    summary="Soumettre les réponses du QCM",
    description="Soumet les réponses en lot et retourne la note finale."
)
def submit_answers(
    qcm_id: int,
    data: QCMSubmissionRequest,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    return qcm_service.evaluate_qcm(db, qcm_id, data.answers)


@router.get(
    "/{qcm_id}/result",
    response_model=QCMResultResponse,
    summary="Consulter le résultat du QCM",
    description="Score pour le candidat ; analyse détaillée (acquis, difficultés) pour l'enseignant et l'admin."
)
def get_qcm_result(
    qcm_id: int,
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
    if not qcm:
        raise ResourceNotFoundException("QCM", qcm_id)

    if principal.role in ["Enseignant", "enseignant", "E"]:
        candidate_service.verify_teacher_access(principal.id, qcm.candidate)

    # Masquer les détails pour le candidat (Section 3.6 : Candidat score seul, Enseignant/Administrateur détail)
    summary = qcm.result_summary if principal.role in ["Enseignant", "enseignant", "E", "Administrateur", "administrateur", "A"] else None

    return QCMResultResponse(
        qcm_id=qcm.id,
        score=qcm.score or 0.0,
        completed=qcm.completed,
        result_summary=summary,
        created_at=qcm.created_at
    )
