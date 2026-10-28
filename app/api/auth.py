from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import User, StudentDetail
from app.schemas.schemas import UserLogin, StudentRegisterRequest, TeacherRegisterRequest, Token, UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentification"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=Token)
def register(reg_data: StudentRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == reg_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    # 1. Create User
    full_name = f"{reg_data.firstName} {reg_data.lastName}".strip()
    user = User(
        email=reg_data.email,
        hashed_password=get_password_hash(reg_data.password),
        name=full_name,
        role="student",
        university=reg_data.university or "ISB",
        field=reg_data.desiredDiploma or "Informatique"
    )
    db.add(user)
    db.flush()

    # 2. Create StudentDetail
    details = StudentDetail(
        user_id=user.id,
        cin_passport=reg_data.cinPassport,
        country=reg_data.country,
        birth_date=reg_data.birthDate,
        sex=reg_data.sex,
        phone=reg_data.phone,
        address=reg_data.address,
        last_diploma=reg_data.lastDiploma,
        diploma_year=reg_data.diplomaYear,
        desired_diploma=reg_data.desiredDiploma,
        level=reg_data.level,
        course_time=reg_data.courseTime,
        known_by=reg_data.knownBy
    )
    db.add(details)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register-teacher", response_model=Token)
def register_teacher(reg_data: TeacherRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == reg_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    full_name = reg_data.name or f"{reg_data.firstName} {reg_data.lastName}".strip()
    user = User(
        email=reg_data.email,
        hashed_password=get_password_hash(reg_data.password),
        name=full_name,
        role="enseignant",
        university=reg_data.university or "ISB",
        field=reg_data.department or reg_data.field or "Informatique"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

