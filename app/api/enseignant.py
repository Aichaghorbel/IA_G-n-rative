from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, Course
from app.schemas.schemas import EnseignantDashboardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/enseignant", tags=["Espace Enseignant"])

@router.get("/dashboard", response_model=EnseignantDashboardResponse)
def get_enseignant_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
   
    return {
     
    }

