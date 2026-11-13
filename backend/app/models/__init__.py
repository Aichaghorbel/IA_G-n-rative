from app.core.database import Base
from app.models.user import User
from app.models.candidate import CandidateProfile, PreRegistration
from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.models.recommendation import Formation, Recommendation
from app.models.qcm import QCM, Question, Answer
from app.models.appointment import Appointment, Notification

__all__ = [
    "Base",
    "User",
    "CandidateProfile",
    "PreRegistration",
    "Conversation",
    "Message",
    "Document",
    "Formation",
    "Recommendation",
    "QCM",
    "Question",
    "Answer",
    "Appointment",
    "Notification"
]
