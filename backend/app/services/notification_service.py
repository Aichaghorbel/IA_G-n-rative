from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.appointment import Notification


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        notif_type: str = "systeme",
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            title=title,
            message=message,
            type=notif_type,
            user_id=user_id,
            session_id=session_id
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
