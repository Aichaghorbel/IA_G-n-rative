from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.session import SessionLinkProposal

# Il n'existe qu'UN SEUL administrateur : il est créé automatiquement au démarrage
# (INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD). L'API ne peut donc créer que des enseignants.
# Les comptes candidats naissent de la conversion d'un visiteur (POST /auth/convert).
STAFF_ROLES = ("Enseignant",)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes en secondes
    refresh_token: Optional[str] = None
    role: str
    user_id: int
    must_change_password: bool = False
    session_link: Optional[SessionLinkProposal] = Field(
        None,
        description="Présent si un en-tête X-Session-Token valide a été envoyé et qu'une conversation "
                    "visiteur peut être associée au profil (à confirmer via POST /auth/session-link).",
    )


class RegisterRequest(BaseModel):
    verification_token: str = Field(..., description="Jeton obtenu via /auth/otp/verify (preuve de possession de l'e-mail)")
    password: str = Field(..., min_length=8, max_length=72)
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    telephone: Optional[str] = Field(None, max_length=30)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    all_devices: bool = Field(False, description="Déconnecte aussi tous les autres appareils")


class SessionResponse(BaseModel):
    session_id: str
    session_token: str
    role: str = "Visiteur"
    expires_in_days: int = 30


class OTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email du candidat pour vérification")


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., pattern=r"^\d{6}$", description="Code OTP à 6 chiffres")


class OTPVerifyResponse(BaseModel):
    message: str
    email: EmailStr
    verified: bool = True
    verification_token: str = Field(..., description="Preuve de possession de l'e-mail (valable 30 min)")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=72)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    role: str = Field("Enseignant", description="Seul le rôle Enseignant est créable (l'administrateur est unique)")
    telephone: Optional[str] = Field(None, max_length=30)

    @field_validator("role")
    @classmethod
    def role_must_be_staff(cls, v: str) -> str:
        from app.core.rbac import Role
        normalized = Role.normalize(v)
        if normalized not in STAFF_ROLES:
            raise ValueError("Rôle invalide : seul « Enseignant » peut être créé (il n'y a qu'un seul administrateur)")
        return normalized


class ConvertVisitorRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    telephone: Optional[str] = Field(None, max_length=30)


class ConvertVisitorResponse(BaseModel):
    message: str
    user_id: int
    email: EmailStr
    temporary_password: Optional[str] = Field(
        None, description="Communiqué une seule fois ; None si le compte existait déjà"
    )
    must_change_password: bool = True


class UserUpdate(BaseModel):
    nom: Optional[str] = Field(None, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    telephone: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    nom: str
    prenom: str
    telephone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    id: int
    email: str
    role: str
    nom: str
    prenom: str
    permissions: List[str] = []
    must_change_password: bool = False
