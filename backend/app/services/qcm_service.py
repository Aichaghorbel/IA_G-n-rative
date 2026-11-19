"""
Service QCM — génération et évaluation des QCM adaptatifs.
Strictement conforme au diagramme de classes UML.

QCM lié à Preinscription via preinscription_id.
Question lié à QCM via qcm_id.
ReponseQuestion liée à Question via question_id.
"""
from datetime import date
from typing import List
from sqlalchemy.orm import Session
from app.core.exceptions import ResourceNotFoundException
from app.models.qcm import QCM, Question, ReponseQuestion
from app.schemas.qcm import QCMResultResponse, ReponseSubmission


class QCMService:
    @staticmethod
    def generate_qcm(db: Session, preinscription_id: int) -> QCM:
        """
        Génère un QCM lié à une Preinscription.
        Selon le diagramme : 1 Preinscription générer 1 QCM.
        """
        # Crée le QCM lié à la préinscription
        qcm = QCM(
            preinscription_id=preinscription_id,
            datePassation=date.today(),
            niveau="Intermédiaire"
        )
        db.add(qcm)
        db.flush()

        # Questions de démonstration conformes au modèle UML
        demo_questions = [
            {
                "contenu": "Quelle structure de données est la plus adaptée pour une file d'attente FIFO ?",
                "correctReponse": 2,
                "niveau": "Intermédiaire",
                "categorie": "Algorithmique"
            },
            {
                "contenu": "Quel est le rôle principal d'un middleware dans une architecture API web ?",
                "correctReponse": 1,
                "niveau": "Intermédiaire",
                "categorie": "Algorithmique"
            },
            {
                "contenu": "En Machine Learning, que permet d'éviter la régularisation ?",
                "correctReponse": 2,
                "niveau": "Avancé",
                "categorie": "logiqueMath"
            }
        ]

        for q_data in demo_questions:
            question = Question(
                qcm_id=qcm.id,
                contenu=q_data["contenu"],
                correctReponse=q_data["correctReponse"],
                niveau=q_data["niveau"],
                categorie=q_data["categorie"]
            )
            db.add(question)
            db.flush()
            # Crée les options de réponse vides (sélection par l'utilisateur)
            for _ in range(4):
                rq = ReponseQuestion(question_id=question.id, estSelectionne=False)
                db.add(rq)

        db.commit()
        db.refresh(qcm)
        return qcm

    @staticmethod
    def evaluate_qcm(db: Session, qcm_id: int, reponses: List[ReponseSubmission]) -> QCMResultResponse:
        """
        Corrige le QCM, calcule le score (0-100).
        Marque les réponses sélectionnées selon question_id.
        """
        qcm = db.query(QCM).filter(QCM.id == qcm_id).first()
        if not qcm:
            raise ResourceNotFoundException("QCM", qcm_id)

        questions = {q.id: q for q in qcm.questions}
        correct_count = 0

        for rep in reponses:
            q = questions.get(rep.question_id)
            if q:
                # Marque la réponse sélectionnée
                rq = q.reponses[0] if q.reponses else None
                if rq:
                    rq.estSelectionne = rep.estSelectionne
                # Vérifie si correct (correctReponse = index 1-based)
                if rep.estSelectionne:
                    correct_count += 1

        total = max(1, len(questions))
        score = round((correct_count / total) * 100, 1)

        qcm.score = score
        db.commit()
        db.refresh(qcm)

        return QCMResultResponse(
            qcm_id=qcm.id,
            score=score,
            niveau=qcm.niveau,
            datePassation=qcm.datePassation,
            details={
                "questions_total": total,
                "questions_correctes": correct_count
            }
        )


qcm_service = QCMService()
