from typing import List

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.visitor_deps import get_visitor_session
from app.core.config import settings
from app.models.visitor_session import VisitorSession as VisitorSessionModel
from app.schemas.session import (
    ProfileUpdate, SessionCreated, SessionInfo, SessionMessage, SessionProfile,
)
from app.services.session_memory_service import session_memory_service
from app.services.session_service import session_service

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une session visiteur anonyme",
    description="Crée une session temporaire sans compte. Renvoyer le jeton dans l'en-tête X-Session-Token.",
)
def create_anonymous_session(request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    session, token = session_service.create_session(db, ip)
    return SessionCreated(
        session_id=str(session.id),
        session_token=token,
        expires_at=session.expires_at,
        expires_in_seconds=settings.VISITOR_SESSION_EXPIRE_DAYS * 86400,
    )


@router.get("/sessions/me", response_model=SessionInfo, summary="Vérifier ma session visiteur")
def get_my_session(session: VisitorSessionModel = Depends(get_visitor_session)):
    return SessionInfo(
        session_id=str(session.id),
        created_at=session.created_at,
        last_seen_at=session.last_seen_at,
        expires_at=session.expires_at,
        message_count=session.user_message_count,
        is_identified=session.candidate_id is not None,
    )


@router.delete("/sessions/me", status_code=status.HTTP_204_NO_CONTENT,
               summary="Terminer ma session et effacer mes données (RGPD)")
def delete_my_session(
    session: VisitorSessionModel = Depends(get_visitor_session),
    db: Session = Depends(get_db),
):
    session_service.delete_session(db, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions/me/messages", response_model=List[SessionMessage],
            summary="Messages récents de ma session")
def get_my_messages(
    session: VisitorSessionModel = Depends(get_visitor_session),
    db: Session = Depends(get_db),
):
    return session_memory_service.get_messages(db, session)


@router.get("/sessions/me/profile", response_model=SessionProfile,
            summary="Profil mémorisé pendant la session")
def get_my_profile(session: VisitorSessionModel = Depends(get_visitor_session)):
    return SessionProfile(profile=session.profile or {})


@router.patch("/sessions/me/profile", response_model=SessionProfile,
              summary="Mettre à jour le profil mémorisé")
def update_my_profile(
    data: ProfileUpdate,
    session: VisitorSessionModel = Depends(get_visitor_session),
    db: Session = Depends(get_db),
):
    profile = session_memory_service.update_profile(db, session, data.model_dump(exclude_none=True))
    return SessionProfile(profile=profile)