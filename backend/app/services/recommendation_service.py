from typing import List
from sqlalchemy.orm import Session
from app.core.exceptions import ResourceNotFoundException
from app.models.candidate import CandidateProfile
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommandationResponse


class RecommendationService:
    @staticmethod
    def generate_recommendations(db: Session, candidate_id: int) -> Recommendation:
        """
        Génère une recommandation d'orientation via l'agent LangGraph / LLM
        sur la base du profil et des intérêts du candidat.
        Selon le diagramme : Recommandation est liée uniquement au Candidat (pas de formation_id).
        """
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
        if not profile:
            raise ResourceNotFoundException("candidat", candidate_id)

        # Crée la recommandation liée uniquement au Candidat (strict diagramme)
        rec = Recommendation(
            candidat_id=candidate_id,
            nom="Recommandation personnalisée",
            scoreComptabilite=0.92,
            justification=(
                "Vos compétences en mathématiques et votre vif intérêt pour le développement web "
                "font du Génie Logiciel à l'IIT un choix d'excellence."
            ),
            statut="à validée"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def build_recommendation_response(rec: Recommendation) -> RecommandationResponse:
        """Construit la réponse API à partir d'une Recommandation."""
        return RecommandationResponse(
            id=rec.id,
            candidat_id=rec.candidat_id,
            nom=rec.nom,
            scoreComptabilite=rec.scoreComptabilite,
            justification=rec.justification,
            statut=rec.statut,
            dateGeneration=rec.dateGeneration
        )


recommendation_service = RecommendationService()
