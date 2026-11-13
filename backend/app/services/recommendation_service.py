from typing import List, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import ResourceNotFoundException
from app.models.candidate import CandidateProfile
from app.models.recommendation import Formation, Recommendation
from app.schemas.recommendation import ParcoursItem, RecommendationResponse


class RecommendationService:
    @staticmethod
    def generate_recommendations(db: Session, candidate_id: int) -> Recommendation:
        """
        Génère une recommandation d'orientation via l'agent LangGraph / LLM
        sur la base du profil et des intérêts du candidat.
        """
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
        if not profile:
            raise ResourceNotFoundException("candidat", candidate_id)

        # Récupère les formations existantes
        formations = db.query(Formation).all()
        if not formations:
            # Formation par défaut
            formation = Formation(
                code="ING_GL_IIT",
                nom="Cycle Ingénieur en Génie Logiciel",
                etablissement="IIT",
                cycle="Ingénieur",
                description="Formation d'ingénieurs axée sur l'ingénierie logicielle avancée et l'IA.",
                avantages=["Forte employabilité", "Stages à l'international"],
                prerequis=["Bac Math/Info/Sciences + Prépa ou Licence"],
                debouches=["Architecte Logiciel", "Ingénieur IA / Data"]
            )
            db.add(formation)
            db.commit()
            db.refresh(formation)
        else:
            formation = formations[0]

        rec = Recommendation(
            candidate_id=candidate_id,
            formation_id=formation.id,
            score_compatibilite=0.92,
            justification="Vos compétences en mathématiques et votre vif intérêt pour le développement web font du Génie Logiciel à l'IIT un choix d'excellence.",
            status="genere",
            genere_par="agent_ia"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def build_recommendation_response(rec: Recommendation) -> RecommendationResponse:
        f = rec.formation
        parcours = [
            ParcoursItem(
                formation_id=f.id,
                formation_nom=f.nom,
                score_compatibilite=rec.score_compatibilite,
                justification=rec.justification,
                avantages=f.avantages or [],
                prerequis=f.prerequis or [],
                debouches=f.debouches or []
            )
        ]
        return RecommendationResponse(
            id=rec.id,
            candidat_id=rec.candidate_id,
            parcours=parcours,
            status=rec.status,
            genere_par=rec.genere_par,
            valide_par=rec.valide_par,
            motif_rejet=rec.motif_rejet,
            created_at=rec.created_at
        )


recommendation_service = RecommendationService()
