"""
Schémas Pydantic pour les QCM, Questions et Réponses.
Strictement conformes au diagramme de classes UML.

QCM -> Questions -> ReponseQuestion (chaîne stricte, aucun lien direct QCM<->Réponse).
QCM est lié à Preinscription uniquement (preinscription_id).
"""
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReponseQuestionDTO(BaseModel):
    """Schéma d'une réponse soumise pour une question."""
    id: Optional[int] = None
    estSelectionne: bool = False

    class Config:
        from_attributes = True


class QuestionDTO(BaseModel):
    """Schéma d'une Question du QCM (sans la bonne réponse, pour éviter la triche)."""
    id: int
    contenu: str
    niveau: str
    categorie: str

    class Config:
        from_attributes = True


class QCMResponse(BaseModel):
    """Schéma de réponse pour un QCM."""
    id: int
    preinscription_id: int
    score: Optional[float] = None
    datePassation: Optional[date] = None
    niveau: Optional[str] = None
    total_questions: int = 0
    questions: List[QuestionDTO] = []

    class Config:
        from_attributes = True


class ReponseSubmission(BaseModel):
    """Soumission d'une réponse à une question (par question_id)."""
    question_id: int
    estSelectionne: bool = True


class QCMSubmissionRequest(BaseModel):
    """Soumission en lot des réponses du QCM."""
    reponses: List[ReponseSubmission]


class QCMResultResponse(BaseModel):
    """Résultat d'un QCM après correction."""
    qcm_id: int
    score: float
    niveau: Optional[str] = None
    datePassation: Optional[date] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Alias de compatibilité pour les imports existants
QCMQuestionDTO = QuestionDTO
AnswerItem = ReponseSubmission
QCMSubmissionRequest = QCMSubmissionRequest
