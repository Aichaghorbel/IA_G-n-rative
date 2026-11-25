from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import AppException
from app.models.appointment import Notification


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        notif_type: str = "Confirmation",
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Notification:
        if user_id is None:
            raise AppException(
                status_code=422,
                code="VALIDATION_FAILED",
                message="user_id est requis pour créer une notification utilisateur",
                details={"field": "user_id"},
            )
        contenu = f"{title}: {message}" if title else message
        notif = Notification(
            type=notif_type or "Confirmation",
            contenu=contenu[:1000],
            dateEnvoi=datetime.now(timezone.utc).replace(tzinfo=None),
            envoyee=True,
            user_id=user_id,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def send_email_template(
        to_email: str,
        subject: str,
        template_name: str,
        variables: Dict[str, Any]
    ) -> bool:
        """
        Simulation ou envoi SMTP (Mailpit local).
        """
        # Dans l'environnement local, la notification est tracée dans les logs et prête pour SMTP
        print(f"[EMAIL DISPATCH] To: {to_email} | Subject: {subject} | Template: {template_name}")
        return True


notification_service = NotificationService()
