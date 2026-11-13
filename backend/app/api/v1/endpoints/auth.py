from typing import List, Optional
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_principal, get_db, require_roles
from app.core.exceptions import InvalidCredentialsException, ResourceNotFoundException
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    OTPRequest,
    OTPVerifyRequest,
    RefreshTokenRequest,
    SessionResponse,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/sessions/anonymous",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une session anonyme (Visiteur)",
    description="Crée une session anonyme avec jeton JWT 30 jours (sliding) pour permettre au visiteur d'utiliser le chatbot."
)
def create_anonymous_session(response: Response):
    session_id, token = auth_service.create_anonymous_session()
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=30 * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return SessionResponse(session_id=session_id, session_token=token)


@router.post(
    "/otp/request",
    summary="Demander un code OTP par email",
    description="Envoie un code OTP à 6 chiffres par email pour vérifier l'adresse du visiteur."
)
def request_otp(data: OTPRequest):
    code = auth_service.request_otp(data.email)
    return {
        "message": "Code OTP généré avec succès",
        "email": data.email,
        "dev_code": code  # visible en dev local pour faciliter les tests
    }


@router.post(
    "/otp/verify",
    summary="Vérifier le code OTP",
    description="Vérifie le code OTP et associe l'email validé à la session."
)
def verify_otp(data: OTPVerifyRequest):
    valid = auth_service.verify_otp(data.email, data.otp_code)
    if not valid:
        raise InvalidCredentialsException(message="Code OTP invalide ou expiré", field="otp_code")
    return {"message": "Email vérifié avec succès", "email": data.email, "verified": True}


@router.post(
    "/login",
    response_model=Token,
    summary="Authentification utilisateur (C, E, A)",
    description="Authentifie un enseignant, un administrateur ou un candidat disposant d'un compte."
)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user, access_token, refresh_token = auth_service.authenticate_user(db, data.email, data.password)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=15 * 60,
        httponly=True,
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=7 * 24 * 3600,
        httponly=True,
        samesite="lax"
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role,
        user_id=user.id
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renouveler le jeton d'accès",
    description="Renouvelle le jeton d'accès (15 min) à partir du refresh token (7 jours)."
)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    new_access_token, new_refresh_token = auth_service.refresh_access_token(db, data.refresh_token)
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        role="Candidat",
        user_id=0
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Déconnexion",
    description="Révoque les tokens de session et supprime les cookies."
)
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("session_token")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/convert",
    summary="Convertir une session visiteur en compte candidat (Interne)",
    description="Convertit une session visiteur OTP vérifiée en compte candidat après admission d'entretien."
)
def convert_visitor(
    session_id: str,
    email: str,
    nom: str,
    prenom: str,
    db: Session = Depends(get_db)
):
    user, temp_pw = auth_service.convert_visitor_to_candidate(
        db=db,
        session_id=session_id,
        email=email,
        nom=nom,
        prenom=prenom
    )
    return {
        "message": "Session convertie en compte candidat",
        "user_id": user.id,
        "email": user.email,
        "temporary_password": temp_pw
    }


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Profil de l'utilisateur connecté",
    description="Retourne le profil de l'utilisateur connecté et ses permissions selon son rôle (Candidat, Enseignant, Administrateur)."
)
def get_me(principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur"))):
    perms = ["read", "write"] if principal.role in ["Administrateur", "administrateur", "A"] else ["read"]
    return MeResponse(
        id=principal.id,
        email=principal.email,
        role=principal.role,
        nom=principal.nom,
        prenom=principal.prenom,
        permissions=perms
    )


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte enseignant (Admin)",
    description="Permet à l'administrateur unifié de créer un compte enseignant."
)
def create_teacher(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("Administrateur"))
):
    user = User(
        email=data.email.lower(),
        hashed_password=get_password_hash(data.password),
        role=data.role,
        nom=data.nom,
        prenom=data.prenom,
        telephone=data.telephone,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Modifier un compte utilisateur (Admin)",
    description="Modifie les informations ou le statut d'un compte (Admin uniquement)."
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("Administrateur"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException("utilisateur", user_id)
    if data.nom is not None:
        user.nom = data.nom
    if data.prenom is not None:
        user.prenom = data.prenom
    if data.telephone is not None:
        user.telephone = data.telephone
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user
