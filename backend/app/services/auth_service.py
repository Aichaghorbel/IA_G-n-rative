import random
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import (
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    ResourceNotFoundException,
    TokenInvalidException
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_visitor_session_token,
    decode_token,
    get_password_hash,
    verify_password
)
from app.models.user import User
from app.models.candidate import CandidateProfile

# Cache temporaire en mémoire des OTP pour le dev local (ou Redis en prod)
OTP_STORE: dict[str, str] = {}


class AuthService:
    @staticmethod
    def create_anonymous_session() -> Tuple[str, str]:
        """Génère un UUID de session et un jeton JWT sliding de 30 jours pour le visiteur."""
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        token = create_visitor_session_token(session_id=session_id)
        return session_id, token

    @staticmethod
    def request_otp(email: str) -> str:
        """Génère un code OTP à 6 chiffres et le stocke (simule l'envoi email)."""
        code = f"{random.randint(100000, 999999)}"
        OTP_STORE[email.lower()] = code
        return code

    @staticmethod
    def verify_otp(email: str, otp_code: str) -> bool:
        """Vérifie le code OTP envoyé par l'utilisateur."""
        stored = OTP_STORE.get(email.lower())
        if stored and stored == otp_code:
            return True
        return False

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Tuple[User, str, str]:
        """Authentifie un utilisateur (C, E, A) et retourne User, access_token, refresh_token."""
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        if not user.is_active:
            raise InvalidCredentialsException(message="Compte désactivé. Veuillez contacter l'administrateur.")

        access_token = create_access_token(subject=user.id, role=user.role, email=user.email)
        refresh_token = create_refresh_token(subject=user.id)
        return user, access_token, refresh_token

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Tuple[str, str]:
        """Renouvelle le jeton d'accès via le refresh token."""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise InvalidRefreshTokenException()
            user_id = int(payload.get("sub"))
        except Exception:
            raise InvalidRefreshTokenException()

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise InvalidRefreshTokenException()

        new_access_token = create_access_token(subject=user.id, role=user.role, email=user.email)
        new_refresh_token = create_refresh_token(subject=user.id)
        return new_access_token, new_refresh_token

    @staticmethod
    def convert_visitor_to_candidate(
        db: Session,
        session_id: str,
        email: str,
        nom: str,
        prenom: str,
        telephone: Optional[str] = None
    ) -> Tuple[User, str]:
        """
        Conversion automatique visiteur -> candidat (Section 6.8).
        Crée le compte utilisateur candidat, rattache le profil et génère un mot de passe temporaire.
        """
        temp_password = f"Smart@{random.randint(1000, 9999)}!"
        hashed_password = get_password_hash(temp_password)

        # Création ou rattachement User
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            user = User(
                email=email.lower(),
                hashed_password=hashed_password,
                role="Candidat",
                nom=nom,
                prenom=prenom,
                telephone=telephone,
                is_active=True
            )
            db.add(user)
            db.flush()

        # Rattachement du profil
        profile = db.query(CandidateProfile).filter(CandidateProfile.email == email.lower()).first()
        if not profile:
            profile = db.query(CandidateProfile).filter(CandidateProfile.session_id == session_id).first()

        if profile:
            profile.user_id = user.id
            profile.statut_dossier = "ENTRETIEN_REALISE"
            db.flush()

        db.commit()
        return user, temp_password


auth_service = AuthService()
