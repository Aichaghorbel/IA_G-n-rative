from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.api.deps import PaginationQuery, get_current_principal, get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.models.appointment import Notification
from app.schemas.notification import (
    NotificationResponse,
    SendEmailRequest,
    SendNotificationRequest
)
from app.services.notification_service import notification_service

router = APIRouter()


@router.get(
    "/notifications",
    response_model=List[NotificationResponse],
    summary="Mes notifications non lues",
    description="Liste paginée des notifications de l'utilisateur."
)
def get_my_notifications(
    response: Response,
    pagination: PaginationQuery = Depends(),
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == principal.id)
    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    return query.order_by(Notification.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()


@router.patch(
    "/notifications/{notification_id}/read",
    summary="Marquer une notification comme lue",
    description="Marque une notification spécifique comme lue."
)
def mark_notification_read(
    notification_id: int,
    principal=Depends(require_roles("Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise ResourceNotFoundException("notification", notification_id)
    notif.is_read = True
    db.commit()
    return {"message": "Notification marquée comme lue", "id": notif.id}


@router.post(
    "/notifications/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Diffuser une notification (Admin)",
    description="Envoie une notification in-app selon un modèle autorisé."
)
def send_notification(
    data: SendNotificationRequest,
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    return notification_service.create_notification(
        db=db,
        title=data.title,
        message=data.message,
        notif_type=data.type,
        user_id=data.user_id,
        session_id=data.session_id
    )


@router.post(
    "/emails/send",
    summary="Envoyer un email transactionnel (Admin)",
    description="Envoie un email selon un modèle autorisé (confirmations, relances, invitations RDV)."
)
def send_email(
    data: SendEmailRequest,
    principal=Depends(require_roles("Administrateur"))
):
    success = notification_service.send_email_template(
        to_email=data.to_email,
        subject=data.subject,
        template_name=data.template_name,
        variables=data.variables
    )
    return {"message": "Email expédié avec succès", "to": data.to_email, "status": "sent"}
