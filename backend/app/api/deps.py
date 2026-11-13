import uuid
from typing import Generator, List, Optional, Union
from fastapi import Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.exceptions import (
    InsufficientRoleException,
    TokenExpiredException,
    TokenInvalidException
)
from app.core.rbac import enforcer, Role
from app.core.security import decode_token
from app.models.user import User


class VisitorSession:
    """Représentation d'un visiteur anonyme disposant d'un jeton de session court."""
    def __init__(self, session_id: str, verified_email: Optional[str] = None):
        self.id = 0
        self.session_id = session_id
        self.verified_email = verified_email
        self.role = Role.VISITEUR
        self.nom = "Visiteur"
        self.prenom = "Anonyme"
        self.is_active = True


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_request_id(
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id")
) -> str:
    if x_request_id and x_request_id.strip():
        return x_request_id.strip()
    return f"req_{uuid.uuid4().hex[:12]}"


def get_current_principal(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
) -> Union[User, VisitorSession]:
    """
    Extrait l'identité de l'appelant :
    1. Si Bearer <JWT> fourni -> Utilisateur authentifié (C, E, A)
    2. Si X-Session-Token -> Visiteur anonyme (V)
    3. Si cookie fourni -> fallback
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_session_token:
        token = x_session_token
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    elif "session_token" in request.cookies:
        token = request.cookies.get("session_token")

    if not token:
        # Session visiteur par défaut si route publique/visiteur
        return VisitorSession(session_id=f"sess_{uuid.uuid4().hex[:12]}")

    payload = decode_token(token)
    token_type = payload.get("type", "access")

    if token_type == "session" or Role.normalize(payload.get("role")) == Role.VISITEUR:
        return VisitorSession(
            session_id=payload.get("session_id", f"sess_{uuid.uuid4().hex[:12]}"),
            verified_email=payload.get("verified_email")
        )

    user_id = payload.get("sub")
    if not user_id:
        raise TokenInvalidException()

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise TokenInvalidException("Utilisateur introuvable ou compte inactif")

    return user


def require_roles(*allowed_roles: str):
    """
    Vérifie que le rôle de l'utilisateur fait partie des rôles autorisés (Casbin / RBAC).
    Accepte les rôles en clair : Visiteur, Candidat, Enseignant, Administrateur.
    """
    normalized_allowed = [Role.normalize(r) for r in allowed_roles]

    def role_checker(
        request: Request,
        principal: Union[User, VisitorSession] = Depends(get_current_principal)
    ) -> Union[User, VisitorSession]:
        role = Role.normalize(principal.role)

        # L'administrateur unifié a un accès universel
        if role == Role.ADMINISTRATEUR:
            return principal

        # Casbin RBAC check
        path = request.url.path
        method = request.method
        if not enforcer.enforce(role, path, method):
            if normalized_allowed and role not in normalized_allowed:
                raise InsufficientRoleException(f"Le rôle '{role}' n'a pas accès à cette opération.")

        return principal

    return role_checker


class PaginationQuery:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Numéro de page (1-indexé)"),
        limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
        sort: str = Query("created_at:desc", description="Tri (champ:asc|desc)")
    ):
        self.page = 1 if not isinstance(page, int) else page
        self.limit = 20 if not isinstance(limit, int) else limit
        self.sort = "created_at:desc" if not isinstance(sort, str) else sort
        self.offset = (self.page - 1) * self.limit
