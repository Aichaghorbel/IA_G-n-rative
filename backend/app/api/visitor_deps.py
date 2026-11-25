from typing import Optional

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import TokenInvalidException
from app.models.visitor_session import VisitorSession as VisitorSessionModel
from app.services.session_service import session_service


def get_visitor_session(
    request: Request,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
) -> VisitorSessionModel:
    """Dépendance : charge la session visiteur en base et prolonge son expiration."""
    token = x_session_token or request.cookies.get("session_token")
    if not token or not token.strip():
        raise TokenInvalidException("En-tête X-Session-Token manquant")
    return session_service.authenticate(db, token.strip())