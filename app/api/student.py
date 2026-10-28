from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, Activity
from app.schemas.schemas import StudentDashboardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/student", tags=["Espace Étudiant"])

@router.get("/dashboard", response_model=StudentDashboardResponse)
def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):


    return {
     
    }

