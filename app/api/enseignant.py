from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, Course, Activity
from app.schemas.schemas import (
    EnseignantDashboardResponse,
    CourseResponse,
    CourseCreate,
    CourseUpdate
)
from app.api.deps import require_teacher

router = APIRouter(prefix="/enseignant", tags=["Espace Enseignant"])

@router.get("/dashboard", response_model=EnseignantDashboardResponse)
def get_enseignant_dashboard(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """
    Tableau de bord de l'enseignant connecté :
    - Statistiques sur ses cours
    - Nombre d'étudiants encadrés
    - Activités récentes
    """
    courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    total_students = sum((c.students_count or 0) for c in courses)
    
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .order_by(Activity.created_at.desc())
        .limit(5)
        .all()
    )

    return EnseignantDashboardResponse(
        user=current_user,
        courses_count=len(courses),
        total_students=total_students,
        courses=courses,
        recent_activities=activities,
        message=f"Bienvenue Professeur {current_user.name}"
    )

@router.get("/courses", response_model=List[CourseResponse])
def get_my_courses(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Lister tous les cours associés à l'enseignant connecté."""
    return db.query(Course).filter(Course.teacher_id == current_user.id).all()

@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Créer un nouveau cours pour l'enseignant connecté."""
    new_course = Course(
        code=course_data.code,
        name=course_data.name,
        schedule=course_data.schedule,
        room=course_data.room,
        students_count=course_data.students_count or 0,
        teacher_id=current_user.id
    )
    db.add(new_course)
    
    # Enregistrer l'activité
    activity = Activity(
        user_id=current_user.id,
        action=f"Création du cours {course_data.code} - {course_data.name}",
        type="doc"
    )
    db.add(activity)
    
    db.commit()
    db.refresh(new_course)
    return new_course

@router.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Mettre à jour les informations d'un cours appartenant à l'enseignant."""
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.teacher_id == current_user.id)
        .first()
    )
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cours non trouvé ou vous n'avez pas l'autorisation de le modifier"
        )
    
    if course_data.code is not None:
        course.code = course_data.code
    if course_data.name is not None:
        course.name = course_data.name
    if course_data.schedule is not None:
        course.schedule = course_data.schedule
    if course_data.room is not None:
        course.room = course_data.room
    if course_data.students_count is not None:
        course.students_count = course_data.students_count

    # Enregistrer l'activité
    activity = Activity(
        user_id=current_user.id,
        action=f"Modification du cours {course.code}",
        type="doc"
    )
    db.add(activity)

    db.commit()
    db.refresh(course)
    return course

@router.delete("/courses/{course_id}")
def delete_course(
    course_id: str,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    """Supprimer un cours appartenant à l'enseignant."""
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.teacher_id == current_user.id)
        .first()
    )
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cours non trouvé ou vous n'avez pas l'autorisation de le supprimer"
        )
    
    code = course.code
    db.delete(course)
    
    activity = Activity(
        user_id=current_user.id,
        action=f"Suppression du cours {code}",
        type="doc"
    )
    db.add(activity)
    
    db.commit()
    return {"status": "success", "message": f"Le cours {code} a été supprimé"}
