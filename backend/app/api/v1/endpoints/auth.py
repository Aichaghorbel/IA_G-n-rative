"""
Authentification & comptes.

Public (sans compte)  : /sessions/anonymous, /otp/request, /otp/verify, /login, /refresh
Utilisateur connecté  : /me, /logout, /change-password
Personnel habilité    : /convert (Enseignant, Administrateur)
Administrateur        : /users (création, liste, modification)
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import (
    PaginationQuery,
    get_authenticated_user,
    get_db,
    require_roles,
)
from app.core.config import settings
from app.core.exceptions import AppException, ResourceNotFoundException
from app.core.rbac import permissions_for
from app.core.security import TOKEN_EMAIL_VERIFIED, create_email_verified_token, decode_token
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ConvertVisitorRequest,
    ConvertVisitorResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    OTPRequest,
    OTPVerifyRequest,
    OTPVerifyResponse,
    RefreshTokenRequest,
    RegisterRequest,
    SessionResponse,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import auth_service
from app.services.otp_service import otp_service
from app.services.session_link_service import session_link_service

router = APIRouter()


def _cookie_opts() -> dict:
    return {"httponly": True, "samesite": settings.COOKIE_SAMESITE, "secure": settings.COOKIE_SECURE}


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie("access_token", access, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **_cookie_opts())
    response.set_cookie(
        "refresh_token", refresh, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=f"{settings.API_V1_STR}/auth", **_cookie_opts()
    )


def _token_response(user: User, access: str, refresh: str) -> Token:
    return Token(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        user_id=user.id,
        must_change_password=bool(user.must_change_password),
    )


# ==============================================================================
# Visiteur sans compte
# ==============================================================================
@router.post(
    "/sessions/anonymous",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une session anonyme (Visiteur)",
    description="Crée une session visiteur persistée (30 jours glissants) pour utiliser le chat sans compte. "
                "Le jeton est à renvoyer dans l'en-tête `X-Session-Token`.",
)
def create_anonymous_session(request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    session_id, token = auth_service.create_anonymous_session(db, ip)
    response.set_cookie(
        "session_token", token, max_age=settings.VISITOR_SESSION_EXPIRE_DAYS * 86400, **_cookie_opts()
    )
    return SessionResponse(
        session_id=session_id, session_token=token,
        expires_in_days=settings.VISITOR_SESSION_EXPIRE_DAYS,
    )


@router.post(
    "/otp/request",
    summary="Demander un code OTP par e-mail",
    description="Envoie un code à 6 chiffres (valable 10 min, 5 essais max, 1 envoi / minute) "
                "pour prouver la possession d'une adresse e-mail.",
)
def request_otp(data: OTPRequest):
    code = otp_service.request(data.email)
    sent = otp_service.send_email(data.email, code)
    body = {"message": "Si l'adresse est valide, un code vous a été envoyé", "email": data.email, "email_sent": sent}
    # Le code n'est jamais renvoyé hors développement
    if settings.DEBUG and settings.ENVIRONMENT.lower() != "production":
        body["dev_code"] = code
    return body


@router.post(
    "/otp/verify",
    response_model=OTPVerifyResponse,
    summary="Vérifier le code OTP",
    description="Valide le code (usage unique) et renvoie un `verification_token` prouvant la possession de l'e-mail.",
)
def verify_otp(data: OTPVerifyRequest):
    otp_service.verify(data.email, data.otp_code)
    return OTPVerifyResponse(
        message="Email vérifié avec succès",
        email=data.email,
        verification_token=create_email_verified_token(data.email),
    )


# ==============================================================================
# Connexion Candidat / Enseignant / Administrateur
# ==============================================================================
@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Créer mon compte candidat (e-mail vérifié par OTP)",
    description="Nécessite le `verification_token` de /auth/otp/verify. Connecte directement le candidat. "
                "Si un `X-Session-Token` valide est envoyé, la réponse contient `session_link` : la proposition "
                "de conserver la conversation de visiteur (à confirmer via POST /auth/session-link).",
)
def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
):
    payload = decode_token(data.verification_token, expected_type=TOKEN_EMAIL_VERIFIED)
    user = auth_service.register_candidate(
        db, email=payload["email"], password=data.password,
        nom=data.nom, prenom=data.prenom, telephone=data.telephone,
    )
    access, refresh = auth_service.issue_tokens(user)
    _set_auth_cookies(response, access, refresh)
    token = _token_response(user, access, refresh)
    raw_session = x_session_token or request.cookies.get("session_token")
    proposal = session_link_service.proposal_for_token(db, user, raw_session)
    if proposal:
        from app.schemas.session import SessionLinkProposal
        token.session_link = SessionLinkProposal(**proposal)
    return token


@router.post(
    "/login",
    response_model=Token,
    summary="Authentification (Candidat, Enseignant, Administrateur)",
    description="Verrouillage temporaire du compte après 5 échecs consécutifs (423). "
                "Si un `X-Session-Token` valide est envoyé par un candidat, la réponse contient `session_link` "
                "(proposition de conserver sa conversation de visiteur).",
)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
):
    user, access, refresh = auth_service.authenticate_user(db, data.email, data.password)
    _set_auth_cookies(response, access, refresh)
    token = _token_response(user, access, refresh)
    raw_session = x_session_token or request.cookies.get("session_token")
    proposal = session_link_service.proposal_for_token(db, user, raw_session)
    if proposal:
        from app.schemas.session import SessionLinkProposal
        token.session_link = SessionLinkProposal(**proposal)
    return token


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renouveler le jeton d'accès",
    description="Rotation : le refresh token fourni est révoqué et un nouveau couple de jetons est émis. "
                "Réutiliser un ancien refresh token coupe toutes les sessions du compte.",
)
def refresh_token(
    response: Response, request: Request, data: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    raw = (data.refresh_token if data else None) or request.cookies.get("refresh_token")
    if not raw:
        from app.core.exceptions import InvalidRefreshTokenException
        raise InvalidRefreshTokenException()
    user, access, refresh = auth_service.refresh_access_token(db, raw)
    _set_auth_cookies(response, access, refresh)
    return _token_response(user, access, refresh)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Déconnexion",
    description="Révoque le jeton d'accès et le refresh token ; `all_devices=true` invalide toutes les sessions.",
)
def logout(
    request: Request,
    data: LogoutRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    authorization = request.headers.get("Authorization", "")
    access = authorization[7:].strip() if authorization.lower().startswith("bearer ") else request.cookies.get("access_token")
    refresh = (data.refresh_token if data else None) or request.cookies.get("refresh_token")
    auth_service.revoke_token(db, access)
    auth_service.revoke_token(db, refresh)
    if data and data.all_devices:
        auth_service.logout_everywhere(db, user)

    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token", path=f"{settings.API_V1_STR}/auth")
    resp.delete_cookie("session_token")
    return resp


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Profil de l'utilisateur connecté",
    description="Profil et permissions fonctionnelles selon le rôle.",
)
def get_me(user: User = Depends(get_authenticated_user)):
    return MeResponse(
        id=user.id, email=user.email, role=user.role, nom=user.nom, prenom=user.prenom,
        permissions=permissions_for(user.role),
        must_change_password=bool(user.must_change_password),
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Changer mon mot de passe",
    description="Obligatoire à la première connexion d'un candidat converti. Déconnecte les autres appareils.",
)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    auth_service.change_password(db, user, data.current_password, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# Conversion visiteur -> candidat (personnel habilité uniquement)
# ==============================================================================
@router.post(
    "/convert",
    response_model=ConvertVisitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convertir un visiteur en compte candidat (Enseignant / Administrateur)",
    description="Crée le compte Candidat avec un mot de passe temporaire aléatoire "
                "(changement obligatoire à la première connexion).",
)
def convert_visitor(
    data: ConvertVisitorRequest,
    db: Session = Depends(get_db),
    staff=Depends(require_roles("Enseignant", "Administrateur")),
):
    user, temp_pw = auth_service.convert_visitor_to_candidate(
        db=db, session_id=data.session_id, email=data.email,
        nom=data.nom, prenom=data.prenom, telephone=data.telephone,
    )
    return ConvertVisitorResponse(
        message="Session convertie en compte candidat" if temp_pw else "Compte candidat existant rattaché",
        user_id=user.id, email=user.email, temporary_password=temp_pw,
        must_change_password=bool(user.must_change_password),
    )


# ==============================================================================
# Gestion des comptes (Administrateur)
# ==============================================================================
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte enseignant (Admin)",
    description="Crée un compte Enseignant (mot de passe temporaire à changer à la première connexion). "
                "L'administrateur est unique et créé automatiquement au démarrage : il ne peut pas être créé ici.",
)
def create_staff_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("Administrateur")),
):
    return auth_service.create_user(
        db, email=data.email, password=data.password, role=data.role,
        nom=data.nom, prenom=data.prenom, telephone=data.telephone,
        must_change_password=True,
    )


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="Lister les comptes (Admin)",
)
def list_users(
    response: Response,
    pagination: PaginationQuery = Depends(),
    db: Session = Depends(get_db),
    admin=Depends(require_roles("Administrateur")),
):
    query = db.query(User)
    response.headers["X-Total-Count"] = str(query.count())
    return query.order_by(User.id.asc()).offset(pagination.offset).limit(pagination.limit).all()


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Modifier un compte utilisateur (Admin)",
    description="Modifie les informations ou active/désactive un compte (désactiver coupe ses sessions en cours).",
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("Administrateur")),
):
    user = db.get(User, user_id)
    if not user:
        raise ResourceNotFoundException("utilisateur", user_id)
    if data.is_active is False and user.id == admin.id:
        raise AppException(status_code=409, code="AUTH_011", message="Vous ne pouvez pas désactiver votre propre compte")

    if data.nom is not None:
        user.nom = data.nom
    if data.prenom is not None:
        user.prenom = data.prenom
    if data.telephone is not None:
        user.telephone = data.telephone
    if data.is_active is not None and data.is_active != user.is_active:
        auth_service.set_active(db, user, data.is_active)
    db.commit()
    db.refresh(user)
    return user
