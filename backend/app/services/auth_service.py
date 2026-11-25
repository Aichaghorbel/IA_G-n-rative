"""Service d'authentification : connexion, jetons, révocation, comptes et conversion."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AccountLockedException,
    AppException,
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidRefreshTokenException,
    TokenExpiredException,
    TokenInvalidException,
    WeakPasswordException,
)
from app.core.security import (
    TOKEN_ACCESS,
    TOKEN_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_temporary_password,
    get_password_hash,
    password_policy_errors,
    verify_password,
)
from app.services.candidate_service import merge_candidats
from app.models.candidate import Candidat, Visiteur
from app.models.conversation import Conversation
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.models.visitor_session import VisitorSession
from app.services.session_service import session_service


def utcnow() -> datetime:
    """UTC naïf, cohérent avec les colonnes TIMESTAMP."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def assert_strong_password(password: str) -> None:
    missing = password_policy_errors(password)
    if missing:
        raise WeakPasswordException(missing)


class AuthService:
    # ------------------------------------------------------------------ visiteurs
    @staticmethod
    def create_anonymous_session(db: Session, client_ip: Optional[str]) -> Tuple[str, str]:
        """
        Session visiteur (sans compte) : enregistrée en base, jeton 30 j glissants.
        Un seul mécanisme de session pour tout le backend (voir session_service).
        """
        session, token = session_service.create_session(db, client_ip)
        return str(session.id), token

    # ------------------------------------------------------------------ connexion
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Tuple[User, str, str]:
        """
        Authentifie un utilisateur (Candidat, Enseignant, Administrateur).
        - message d'erreur identique que l'e-mail existe ou non (anti-énumération) ;
        - verrouillage temporaire après LOGIN_MAX_ATTEMPTS échecs consécutifs.
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        now = utcnow()

        if user and user.locked_until and user.locked_until > now:
            raise AccountLockedException(int((user.locked_until - now).total_seconds()) + 1)

        password_ok = verify_password(password, user.hashed_password if user else None)

        if not user or not password_ok:
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                    user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
                    user.failed_login_attempts = 0
                db.commit()
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InvalidCredentialsException(message="Compte désactivé. Veuillez contacter l'administrateur.")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        db.commit()

        access_token, refresh_token = AuthService.issue_tokens(user)
        return user, access_token, refresh_token

    @staticmethod
    def issue_tokens(user: User) -> Tuple[str, str]:
        tv = user.token_version or 0
        access = create_access_token(subject=user.id, role=user.role, email=user.email, token_version=tv)
        refresh = create_refresh_token(subject=user.id, token_version=tv)
        return access, refresh

    # ------------------------------------------------------------------ révocation
    @staticmethod
    def is_revoked(db: Session, jti: Optional[str]) -> bool:
        if not jti:
            return False
        return db.get(RevokedToken, jti) is not None

    @staticmethod
    def revoke_token(db: Session, token: Optional[str]) -> None:
        """Révoque un jeton (déconnexion). Silencieux si le jeton est déjà invalide/expiré."""
        if not token:
            return
        try:
            payload = decode_token(token)
        except (TokenExpiredException, TokenInvalidException):
            return
        jti = payload.get("jti")
        if not jti or db.get(RevokedToken, jti):
            return
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
        db.add(RevokedToken(jti=jti, expires_at=exp))
        # Purge opportuniste des entrées dont le jeton serait de toute façon expiré
        db.query(RevokedToken).filter(RevokedToken.expires_at < utcnow()).delete(synchronize_session=False)
        db.commit()

    @staticmethod
    def logout_everywhere(db: Session, user: User) -> None:
        """Invalide tous les jetons existants de l'utilisateur."""
        user.token_version = (user.token_version or 0) + 1
        db.commit()

    # ------------------------------------------------------------------ refresh
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Tuple[User, str, str]:
        """Rotation : l'ancien refresh token est révoqué, un nouveau couple est émis."""
        try:
            payload = decode_token(refresh_token, expected_type=TOKEN_REFRESH)
            user_id = int(payload.get("sub"))
        except Exception:
            raise InvalidRefreshTokenException()

        if AuthService.is_revoked(db, payload.get("jti")):
            # Réutilisation d'un refresh déjà consommé : possible vol → on coupe toutes les sessions
            user = db.get(User, user_id)
            if user:
                AuthService.logout_everywhere(db, user)
            raise InvalidRefreshTokenException()

        user = db.get(User, user_id)
        if not user or not user.is_active or (payload.get("tv", 0) != (user.token_version or 0)):
            raise InvalidRefreshTokenException()

        AuthService.revoke_token(db, refresh_token)
        access, refresh = AuthService.issue_tokens(user)
        return user, access, refresh

    # ------------------------------------------------------------------ comptes
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsException(message="Mot de passe actuel incorrect", field="current_password")
        assert_strong_password(new_password)
        if verify_password(new_password, user.hashed_password):
            raise WeakPasswordException(["un mot de passe différent de l'ancien"])
        user.hashed_password = get_password_hash(new_password)
        user.must_change_password = False
        user.token_version = (user.token_version or 0) + 1  # déconnecte les autres appareils
        db.commit()

    @staticmethod
    def create_user(
        db: Session, *, email: str, password: str, role: str, nom: str, prenom: str,
        telephone: Optional[str] = None, must_change_password: bool = False,
    ) -> User:
        email = email.lower()
        if role == "Administrateur":
            # Administrateur unique : créé uniquement au démarrage de l'application
            raise AppException(status_code=403, code="AUTH_012",
                               message="L'administrateur est unique : aucun autre ne peut être créé")
        if db.query(User).filter(User.email == email).first():
            raise EmailAlreadyExistsException(email)
        assert_strong_password(password)
        user = User(
            email=email, hashed_password=get_password_hash(password), role=role,
            nom=nom, prenom=prenom, telephone=telephone, is_active=True,
            must_change_password=must_change_password,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def register_candidate(
        db: Session, *, email: str, password: str, nom: str, prenom: str,
        telephone: Optional[str] = None,
    ) -> User:
        """Auto-inscription d'un candidat (e-mail prouvé par OTP). Crée User + Candidat atomiquement."""
        email = email.lower()
        if db.query(User).filter(User.email == email).first():
            raise EmailAlreadyExistsException(email)
        assert_strong_password(password)
        user = User(
            email=email, hashed_password=get_password_hash(password), role="Candidat",
            nom=nom, prenom=prenom, telephone=telephone, is_active=True,
            must_change_password=False,
        )
        db.add(user)
        db.flush()
        db.add(Candidat(user_id=user.id))
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_active(db: Session, user: User, active: bool) -> None:
        user.is_active = active
        if not active:
            user.token_version = (user.token_version or 0) + 1  # coupe les sessions en cours
        db.commit()

    # ------------------------------------------------------------------ conversion
    @staticmethod
    def convert_visitor_to_candidate(
        db: Session, session_id: str, email: str, nom: str, prenom: str,
        telephone: Optional[str] = None,
    ) -> Tuple[User, Optional[str]]:
        """
        Conversion visiteur -> candidat (Section 6.8).
        Crée le compte Candidat (mot de passe temporaire aléatoire, changement forcé à la
        première connexion) et rattache le Visiteur à son Candidat.
        Retourne (user, mot_de_passe_temporaire) — None si le compte existait déjà.
        """
        email = email.lower()
        user = db.query(User).filter(User.email == email).first()
        temp_password: Optional[str] = None

        if user is None:
            temp_password = generate_temporary_password()
            user = User(
                email=email, hashed_password=get_password_hash(temp_password), role="Candidat",
                nom=nom, prenom=prenom, telephone=telephone, is_active=True,
                must_change_password=True,
            )
            db.add(user)
            db.flush()
        elif user.role != "Candidat":
            # On ne « convertit » jamais un compte du personnel en candidat
            raise EmailAlreadyExistsException(email)

        visiteur = db.query(Visiteur).filter(Visiteur.sessionToken == session_id).first()
        candidat = db.query(Candidat).filter(Candidat.user_id == user.id).first()
        visiteur_cand = (
            db.query(Candidat).filter(Candidat.visiteur_id == visiteur.id).first()
            if visiteur is not None else None
        )
        if candidat is None and visiteur_cand is not None:
            if visiteur_cand.user_id is not None and visiteur_cand.user_id != user.id:
                raise EmailAlreadyExistsException(email)
            candidat = visiteur_cand
        elif candidat is not None and visiteur_cand is not None and visiteur_cand.id != candidat.id:
            if visiteur_cand.user_id is None:
                merge_candidats(db, visiteur_cand, candidat)
            else:
                raise EmailAlreadyExistsException(email)

        if candidat is None:
            candidat = Candidat(visiteur_id=visiteur.id if visiteur else None)
            db.add(candidat)
        candidat.user_id = user.id
        if visiteur and not candidat.visiteur_id:
            candidat.visiteur_id = visiteur.id
        db.flush()

        if visiteur is not None:
            db.query(Conversation).filter(
                Conversation.visiteur_id == visiteur.id, Conversation.candidat_id.is_(None)
            ).update({Conversation.candidat_id: candidat.id}, synchronize_session=False)

        try:
            import uuid as _uuid
            vs_uuid = _uuid.UUID(str(session_id))
            vs = db.get(VisitorSession, vs_uuid)
            if vs is not None and vs.candidate_id is None:
                vs.candidate_id = candidat.id
        except (ValueError, TypeError):
            pass

        db.commit()
        db.refresh(user)
        return user, temp_password


auth_service = AuthService()
