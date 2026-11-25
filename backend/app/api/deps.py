"""
Dépendances FastAPI : base de données, identité de l'appelant (authentification) et
contrôle des rôles (autorisation).

Modèle d'identité
-----------------
* Utilisateur connecté (Candidat / Enseignant / Administrateur) : en-tête
  ``Authorization: Bearer <access_token>`` (ou cookie httpOnly ``access_token``).
* Visiteur sans compte : en-tête ``X-Session-Token`` (ou cookie ``session_token``).
* Aucun jeton : visiteur « éphémère ». Il peut utiliser le chat : une session est alors
  créée automatiquement et son jeton est renvoyé dans l'en-tête de réponse ``X-Session-Token``.

Règles de sécurité appliquées
-----------------------------
* un refresh token ne peut JAMAIS servir de jeton d'accès (types de jetons stricts) ;
* un jeton révoqué (déconnexion) ou émis avant un changement de mot de passe /
  une désactivation du compte est refusé ;
* le rôle est relu en base à chaque requête (pas de confiance au rôle du jeton) ;
* ``require_roles`` refuse par défaut : 401 si non authentifié, 403 si rôle insuffisant.
"""
import uuid
from typing import Generator, Optional, Union

from fastapi import Depends, Header, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import (
    AppException,
    InsufficientRoleException,
    TokenInvalidException,
)
from app.core.rbac import Role
from app.core.security import TOKEN_ACCESS, TOKEN_SESSION, decode_token
from app.models.user import User
from app.services.auth_service import auth_service
from app.services.session_service import session_service

# Routes accessibles même quand l'utilisateur doit d'abord changer son mot de passe
_PASSWORD_CHANGE_ALLOWED_SUFFIXES = ("/auth/change-password", "/auth/me", "/auth/logout")


class VisitorSession:
    """Visiteur anonyme (avec ou sans session persistée)."""

    def __init__(
        self,
        session_id: Optional[str],
        verified_email: Optional[str] = None,
        is_ephemeral: bool = False,
    ):
        self.id = 0
        self.session_id = session_id
        self.verified_email = verified_email
        self.is_ephemeral = is_ephemeral  # True = aucun jeton fourni
        self.role = Role.VISITEUR
        self.nom = "Visiteur"
        self.prenom = "Anonyme"
        self.email = None
        self.is_active = True
        self.must_change_password = False


Principal = Union[User, VisitorSession]


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


def _extract_token(
    request: Request, authorization: Optional[str], x_session_token: Optional[str]
) -> Optional[str]:
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
        raise TokenInvalidException("En-tête Authorization invalide (format attendu : Bearer <jeton>)")
    # Un utilisateur connecté via cookie (ex. après /auth/register ou /auth/login) garde la priorité
    # sur un éventuel en-tête X-Session-Token résiduel (nécessaire notamment pour /auth/session-link).
    access_cookie = request.cookies.get("access_token")
    if access_cookie:
        return access_cookie.strip()
    if x_session_token:
        return x_session_token.strip()
    return request.cookies.get("session_token")


def get_current_principal(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
) -> Principal:
    """Identifie l'appelant : utilisateur authentifié, visiteur avec session, ou visiteur éphémère."""
    token = _extract_token(request, authorization, x_session_token)
    if not token:
        return VisitorSession(session_id=None, is_ephemeral=True)

    payload = decode_token(token)  # signature + expiration (401 sinon)
    token_type = payload.get("type")

    # --- Visiteur avec session persistée --------------------------------------
    if token_type == TOKEN_SESSION:
        session = session_service.authenticate(db, token)  # vérifie la base + prolonge (sliding)
        return VisitorSession(
            session_id=str(session.id), verified_email=payload.get("verified_email")
        )

    # --- Utilisateur connecté : uniquement un jeton d'ACCÈS -------------------
    if token_type != TOKEN_ACCESS:
        raise TokenInvalidException("Ce type de jeton ne permet pas d'accéder à cette ressource")

    if auth_service.is_revoked(db, payload.get("jti")):
        raise TokenInvalidException("Jeton révoqué : veuillez vous reconnecter")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise TokenInvalidException()

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise TokenInvalidException("Utilisateur introuvable ou compte inactif")
    if payload.get("tv", 0) != (user.token_version or 0):
        raise TokenInvalidException("Session expirée (mot de passe modifié ou accès retiré)")
    return user


def get_authenticated_user(principal: Principal = Depends(get_current_principal)) -> User:
    """Exige un utilisateur connecté (pas un visiteur). N'applique pas le changement de mot de passe forcé."""
    if isinstance(principal, VisitorSession):
        raise TokenInvalidException("Authentification requise")
    return principal


def _check_roles(request: Request, principal: Principal, allowed: set) -> Principal:
    role = Role.normalize(principal.role)

    is_admin = role == Role.ADMINISTRATEUR  # l'administrateur unifié a un accès transverse
    if not is_admin and role not in allowed:
        if isinstance(principal, VisitorSession) and principal.is_ephemeral:
            # Non authentifié : 401 (le client doit se connecter), pas 403
            raise TokenInvalidException("Authentification requise pour cette ressource")
        raise InsufficientRoleException(f"Le rôle '{role}' n'a pas accès à cette opération.")

    if getattr(principal, "must_change_password", False) and not request.url.path.endswith(
        _PASSWORD_CHANGE_ALLOWED_SUFFIXES
    ):
        raise AppException(
            status_code=403,
            code="AUTH_010",
            message="Vous devez changer votre mot de passe temporaire avant de continuer",
            details={"action": "POST /api/v1/auth/change-password"},
        )
    return principal


def require_roles(*allowed_roles: str):
    """
    Autorise uniquement les rôles listés (Visiteur, Candidat, Enseignant, Administrateur).
    Refus par défaut. L'Administrateur est toujours autorisé.
    """
    allowed = {Role.normalize(r) for r in allowed_roles}

    def role_checker(
        request: Request, principal: Principal = Depends(get_current_principal)
    ) -> Principal:
        return _check_roles(request, principal, allowed)

    return role_checker


def chat_access(*allowed_roles: str):
    """
    Accès au chat : libre pour les visiteurs SANS compte.
    Si aucun jeton n'est fourni, une session visiteur est créée à la volée et son jeton
    est renvoyé dans l'en-tête ``X-Session-Token`` (et en cookie httpOnly).
    """
    allowed = {Role.normalize(r) for r in (allowed_roles or (Role.VISITEUR, Role.CANDIDAT))}

    def checker(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if isinstance(principal, VisitorSession) and principal.is_ephemeral:
            ip = request.client.host if request.client else None
            session, token = session_service.create_session(db, ip)
            response.headers["X-Session-Token"] = token
            response.set_cookie(
                "session_token", token,
                max_age=settings.VISITOR_SESSION_EXPIRE_DAYS * 86400,
                httponly=True, samesite=settings.COOKIE_SAMESITE, secure=settings.COOKIE_SECURE,
            )
            principal = VisitorSession(session_id=str(session.id))
        return _check_roles(request, principal, allowed)

    return checker


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
