from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, Field


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SendNotificationRequest(BaseModel):
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=2000)
    type: str = Field("systeme", description="confirmation, relance, rdv, systeme")


class SendEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str = Field(..., max_length=200)
    template_name: str = Field(..., description="confirmation_preinscription, invitation_rdv, code_otp, relance")
    variables: Dict[str, Any] = Field(default_factory=dict)
