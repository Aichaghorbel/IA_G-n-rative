"""
SA-29 — Association de la session visiteur au profil candidat.

Le candidat doit envoyer DEUX en-têtes :
  Authorization: Bearer <access_token>   (il est identifié)
  X-Session-Token: <session_token>       (preuve qu'il détient la session visiteur)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.api.ownership import get_candidat_of
from app.api.visitor_deps import get_visitor_session
from app.core.exceptions import ResourceNotFoundException
from app.models.visitor_session import VisitorSession as VisitorSessionModel
from app.schemas.session import SessionLinkProposal, SessionLinkRequest, SessionLinkResult
from app.services.session_link_service import session_link_service

router = APIRouter()


def _candidat_or_404(db: Session, principal):
    candidat = get_candidat_of(db, principal)
    if candidat is None:
        raise ResourceNotFoundException("profil candidat", principal.id)
    return candidat


@router.get(
    "/proposal",
    response_model=SessionLinkProposal,
    summary="Proposition d'association de ma conversation de visiteur à mon profil",
    description="À appeler après connexion, avec `Authorization: Bearer` ET `X-Session-Token`. "
                "Lecture seule : décrit ce qui serait associé, ne modifie rien.",
)
def get_link_proposal(
    principal=Depends(require_roles("Candidat")),
    session: VisitorSessionModel = Depends(get_visitor_session),
    db: Session = Depends(get_db),
):
    candidat = _candidat_or_404(db, principal)
    return SessionLinkProposal(**session_link_service.proposal(db, candidat, session))


@router.post(
    "",
    response_model=SessionLinkResult,
    summary="Associer ma session visiteur à mon profil candidat (avec accord explicite)",
    description="Exige `consent=true` et que `session_id` corresponde au jeton `X-Session-Token`. "
                "Idempotent. 409 si la session appartient déjà à un autre candidat.",
)
def link_session(
    data: SessionLinkRequest,
    principal=Depends(require_roles("Candidat")),
    session: VisitorSessionModel = Depends(get_visitor_session),
    db: Session = Depends(get_db),
):
    candidat = _candidat_or_404(db, principal)
    return SessionLinkResult(
        **session_link_service.link(db, candidat, session, data.session_id, data.consent)
    )
