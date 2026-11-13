from typing import List, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import ResourceNotFoundException
from app.models.candidate import CandidateProfile
from app.models.qcm import QCM, Question, Answer
from app.schemas.qcm import AnswerItem, QCMResponse, QCMQuestionDTO, QCMResultResponse


class QCMService:
    @staticmethod
    def generate_qcm(db: Session, candidate_id: int, formation_id: int = None) -> QCM:
        """Génère un QCM adaptatif personnalisé (5 questions)."""
        qcm = QCM(
            candidate_id=candidate_id,
            formation_id=formation_id,
            total_questions=3,
            completed=False
        )
        db.add(qcm)
        db.flush()

        # Questions de démonstration
        demo_questions = [
            (
                "Quelle structure de données est la plus adaptée pour une file d'attente FIFO ?",
                ["Pile (Stack)", "File (Queue)", "Tableau statique", "Arbre binaire"],
                1,
                "facile"
            ),
            (
                "Quel est le rôle principal d'un middleware dans une architecture API web ?",
                ["Stocker les données en base", "Intercepter et traiter les requêtes HTTP avant les routes", "Compiler le code frontend", "Générer les certificats SSL"],
                1,
                "moyen"
            ),
            (
                "En Machine Learning, que permet d'éviter la régularisation ?",
                ["Le sous-apprentissage (underfitting)", "Le sur-apprentissage (overfitting)", "Le manque de mémoire vive", "La latence réseau"],
                1,
                "moyen"
            )
        ]

        for text, opts, correct, diff in demo_questions:
            q = Question(
                qcm_id=qcm.id,
                question_text=text,
                options=opts,
                correct_option=correct,
                difficulty=diff
            )
            db.add(q)

        db.commit()
        db.refresh(qcm)
        return qcm

    @staticmethod
    def evaluate_qcm(db: Session, qcm_id: int, answers: List[AnswerItem]) -> QCMResultResponse:
        """Corrige le QCM, calcule le score et analyse les acquis/difficultés."""
        qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
        if not qcm:
            raise ResourceNotFoundException("qcm", qcm_id)

        questions = {q.id: q for q in qcm.questions}
        correct_count = 0

        for ans in answers:
            q = questions.get(ans.question_id)
            if q:
                is_corr = (q.correct_option == ans.selected_option)
                if is_corr:
                    correct_count += 1
                answer_record = Answer(
                    qcm_id=qcm.id,
                    question_id=q.id,
                    selected_option=ans.selected_option,
                    is_correct=is_corr
                )
                db.add(answer_record)

        total = max(1, len(questions))
        final_score = round((correct_count / total) * 100, 1)

        qcm.score = final_score
        qcm.completed = True
        qcm.result_summary = {
            "acquis": ["Algorithmique de base", "Conception d'APIs"] if final_score >= 50 else ["Motivation confirmée"],
            "difficultes": ["Concepts avancés d'apprentissage automatique"] if final_score < 70 else [],
            "motivations": "Très motivé pour le cursus ingénieur et les projets appliqués"
        }

        # Mise à jour du statut du candidat -> QCM_FAIT
        candidate = db.query(CandidateProfile).filter(CandidateProfile.id == qcm.candidate_id).first()
        if candidate and candidate.statut_dossier in ["PREINSCRIT", "PROFIL_ENRICHI"]:
            candidate.statut_dossier = "QCM_FAIT"

        db.commit()
        db.refresh(qcm)

        return QCMResultResponse(
            qcm_id=qcm.id,
            score=qcm.score,
            completed=qcm.completed,
            result_summary=qcm.result_summary,
            created_at=qcm.created_at
        )


qcm_service = QCMService()
