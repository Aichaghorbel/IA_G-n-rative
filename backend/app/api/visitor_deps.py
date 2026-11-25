from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import TokenInvalidException
from app.models.visitor_session import VisitorSession as VisitorSessionModel
from app.services.session_service import session_service


def get_visitor_session(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
) -> VisitorSessionModel:
    """Dépendance : charge la session visiteur en base et prolonge son expiration."""
    if not x_session_token:
        raise TokenInvalidException("En-tête X-Session-Token manquant")
    return session_service.authenticate(db, x_session_token)