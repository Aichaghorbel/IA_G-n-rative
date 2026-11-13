from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
    refresh_token: Optional[str] = None
    role: str
    user_id: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class SessionResponse(BaseModel):
    session_id: str
    session_token: str
    role: str = "Visiteur"
    expires_in_days: int = 30


class OTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email du candidat pour vérification")


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(..., min_length=4, max_length=6, description="Code OTP à 6 chiffres")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    nom: str = Field(..., max_length=100)
    prenom: str = Field(..., max_length=100)
    role: str = Field("Enseignant", description="Rôle créé par l'admin (Enseignant)")
    telephone: Optional[str] = None


class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
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
    permissions: list[str] = []
