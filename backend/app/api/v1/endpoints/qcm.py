"""
Endpoints API pour les QCM adaptatifs.
Strictement conformes au diagramme de classes UML.

QCM lié à Preinscription via preinscription_id.
Question lié à QCM. ReponseQuestion liée à Question uniquement.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.ownership import assert_can_access_candidat
from app.api.deps import get_db, require_roles
from app.core.exceptions import AppException, ResourceNotFoundException
from app.core.rbac import Role
from app.models.qcm import QCM, Preinscription
from app.schemas.qcm import (
    QuestionDTO,
    QCMResponse,
    QCMResultResponse,
    QCMSubmissionRequest
)
from app.services.qcm_service import qcm_service

router = APIRouter()


@router.post(
    "",
    response_model=QCMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Générer un QCM lié à une Préinscription",
    description="Génère un QCM adaptatif personnalisé pour la préinscription donnée. Selon le diagramme : 1 Preinscription génère 1 QCM."
)
def generate_qcm(
    preinscription_id: int = Query(..., description="ID de la préinscription"),
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    # Vérifie que la préinscription existe et appartient à l'appelant
    preinscription = db.query(Preinscription).filter(Preinscription.id == preinscription_id).first()
    if not preinscription:
        raise ResourceNotFoundException("préinscription", preinscription_id)
    assert_can_access_candidat(
        db, principal, preinscription.candidat_id,
        resource="préinscription", resource_id=preinscription_id,
    )
    if preinscription.qcm is not None:
        raise AppException(
            status_code=409,
            code="QCM_001",
            message="Un QCM existe déjà pour cette préinscription",
            details={"qcm_id": preinscription.qcm.id, "preinscription_id": preinscription_id},
        )

    qcm = qcm_service.generate_qcm(db, preinscription_id=preinscription_id)

    questions_dto = [
        QuestionDTO(id=q.id, contenu=q.contenu, niveau=q.niveau, categorie=q.categorie)
        for q in qcm.questions
    ]
    return QCMResponse(
        id=qcm.id,
        preinscription_id=qcm.preinscription_id,
        score=qcm.score,
        datePassation=qcm.datePassation,
        niveau=qcm.niveau,
        total_questions=len(questions_dto),
        questions=questions_dto
    )


@router.get(
    "/{qcm_id}",
    response_model=QCMResponse,
    summary="Consulter les questions d'un QCM",
    description="Récupère les questions sans les réponses correctes (pour éviter la triche)."
)
def get_qcm(
    qcm_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
    if not qcm:
        raise ResourceNotFoundException("QCM", qcm_id)
    prereg = db.query(Preinscription).filter(Preinscription.id == qcm.preinscription_id).first()
    if not prereg:
        raise ResourceNotFoundException("QCM", qcm_id)
    assert_can_access_candidat(db, principal, prereg.candidat_id, resource="QCM", resource_id=qcm_id)

    questions_dto = [
        QuestionDTO(id=q.id, contenu=q.contenu, niveau=q.niveau, categorie=q.categorie)
        for q in qcm.questions
    ]
    return QCMResponse(
        id=qcm.id,
        preinscription_id=qcm.preinscription_id,
        score=qcm.score,
        datePassation=qcm.datePassation,
        niveau=qcm.niveau,
        total_questions=len(questions_dto),
        questions=questions_dto
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
    qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
    if not qcm:
        raise ResourceNotFoundException("QCM", qcm_id)
    prereg = db.query(Preinscription).filter(Preinscription.id == qcm.preinscription_id).first()
    if not prereg:
        raise ResourceNotFoundException("QCM", qcm_id)
    assert_can_access_candidat(db, principal, prereg.candidat_id, resource="QCM", resource_id=qcm_id)
    return qcm_service.evaluate_qcm(db, qcm_id, data.reponses)


@router.get(
    "/{qcm_id}/result",
    response_model=QCMResultResponse,
    summary="Consulter le résultat du QCM",
    description="Score pour le candidat ; analyse détaillée pour l'enseignant et l'admin."
)
def get_qcm_result(
    qcm_id: int,
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
    if not qcm:
        raise ResourceNotFoundException("QCM", qcm_id)
    prereg = db.query(Preinscription).filter(Preinscription.id == qcm.preinscription_id).first()
    if not prereg:
        raise ResourceNotFoundException("QCM", qcm_id)
    assert_can_access_candidat(db, principal, prereg.candidat_id, resource="QCM", resource_id=qcm_id)

    # Les détails ne sont visibles que par l'enseignant et l'admin
    details = None
    if Role.normalize(principal.role) in (Role.ENSEIGNANT, Role.ADMINISTRATEUR):
        details = {"questions_total": len(qcm.questions), "score": qcm.score}

    return QCMResultResponse(
        qcm_id=qcm.id,
        score=qcm.score or 0.0,
        niveau=qcm.niveau,
        datePassation=qcm.datePassation,
        details=details
    )
