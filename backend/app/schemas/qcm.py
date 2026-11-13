from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class QCMQuestionDTO(BaseModel):
    id: int
    question_text: str
    options: List[str]
    difficulty: str

    class Config:
        from_attributes = True


class QCMResponse(BaseModel):
    id: int
    candidate_id: int
    formation_id: Optional[int]
    total_questions: int
    questions: List[QCMQuestionDTO]


class AnswerItem(BaseModel):
    question_id: int
    selected_option: int = Field(..., ge=0, le=3)


class QCMSubmissionRequest(BaseModel):
    answers: List[AnswerItem]


class QCMResultResponse(BaseModel):
    qcm_id: int
    score: float
    completed: bool
    # Les détails ne sont visibles que par l'enseignant et l'admin
    result_summary: Optional[Dict[str, List[str]]] = None
    created_at: datetime
