from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class StudentRegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    cinPassport: Optional[str] = None
    country: Optional[str] = None
    birthDate: Optional[str] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lastDiploma: Optional[str] = None
    diplomaYear: Optional[str] = None
    university: Optional[str] = None
    desiredDiploma: Optional[str] = None
    level: Optional[str] = None
    courseTime: Optional[str] = None
    knownBy: Optional[str] = None

class TeacherRegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    name: Optional[str] = None
    phone: Optional[str] = None
    university: Optional[str] = "ISB"
    department: Optional[str] = None
    field: Optional[str] = None
    grade: Optional[str] = None
    specialty: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    university: Optional[str] = None
    field: Optional[str] = None

    class Config:
        from_attributes = True


# --- Activity Schema ---
class ActivityResponse(BaseModel):
    id: str
    action: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Student Dashboard ---
class StudentDashboardResponse(BaseModel):
    user: Optional[UserResponse] = None
    recent_activities: Optional[List[ActivityResponse]] = []
    message: Optional[str] = None


# --- Admin Dashboard ---
class AdminDashboardResponse(BaseModel):
    total_students: Optional[int] = 0
    total_teachers: Optional[int] = 0
    total_courses: Optional[int] = 0
    recent_activities: Optional[List[ActivityResponse]] = []
    message: Optional[str] = None


# --- Enseignant Dashboard ---
class EnseignantDashboardResponse(BaseModel):
    user: Optional[UserResponse] = None
    courses_count: Optional[int] = 0
    total_students: Optional[int] = 0
    recent_activities: Optional[List[ActivityResponse]] = []
    message: Optional[str] = None
