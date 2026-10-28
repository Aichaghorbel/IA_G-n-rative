from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, FAQQuestion
from app.schemas.schemas import AdminDashboardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["Espace Administration"])

@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
   
    return {
  
    }

