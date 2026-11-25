import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import RateLimitExceededException
from app.models.conversation import Conversation, Message, Reponse
from app.schemas.conversation import MessageResponse, MessageSource


class ConversationService:
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Détecte la langue parmi : 'fr' (Français), 'tn' (Tunisien en arabe ou translittéré), 'arabizi' (Arabizi avec chiffres 3, 7, 9, 5).
        """
        text_lower = text.lower()
        # Arabizi pattern: chiffres intégrés comme lettres (3=ayn, 7=ha, 5=kha, 9=qaf)
        arabizi_pattern = re.compile(r"\b\w*[235789]\w*\b")
        if arabizi_pattern.search(text_lower) or any(w in text_lower for w in ["chnowa", "kifech", "wa9tech", "barcha", "3aslema", "n7eb"]):
            return "arabizi"

        # Tunisian dialect en caractères arabes ou mots courants
        tn_keywords = ["شكون", "وقتاش", "كيفاش", "برشا", "عسلامة", "نحب", "فما", "شنوة", "قداش"]
        if any(w in text for w in tn_keywords):
            return "tn"

        return "fr"

    @staticmethod
    def detect_intent(text: str) -> str:
        """Détecte l'intention principale de l'utilisateur."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["preinscr", "préinscr", "dossier", "inscr", "candidat"]):
            return "preinscription"
        elif any(w in text_lower for w in ["rdv", "rendez-vous", "entretien", "date", "creneau"]):
            return "rdv"
        elif any(w in text_lower for w in ["qcm", "quiz", "test", "evaluation", "score"]):
            return "qcm"
        elif any(w in text_lower for w in ["orientation", "conseil", "hesite", "choisir", "mieux"]):
            return "orientation"
        elif any(w in text_lower for w in ["programme", "iit", "isb", "licence", "prepa", "ingénieur", "frais", "debouche"]):
            return "info_programme"
        return "autre"

    @staticmethod
    def assert_rate_limit(db: Session, conversation: Conversation) -> None:
        """Anti-abus du chat ouvert aux visiteurs : N messages / minute / conversation."""
        since = datetime.utcnow() - timedelta(minutes=1)
        recent = (
            db.query(func.count(Message.idMessage))
            .filter(Message.conversation_id == conversation.idConversation, Message.dateEnvoi >= since)
            .scalar()
        )
        if recent >= settings.SESSION_MESSAGES_PER_MINUTE:
            raise RateLimitExceededException(retry_after=60, limit=settings.SESSION_MESSAGES_PER_MINUTE)

    @staticmethod
    def process_message(
        db: Session,
        conversation: Conversation,
        user_text: str
    ) -> MessageResponse:
        """
        Traite un message (Visiteur ou Candidat) selon le diagramme de classes :
        Message (question) -> 1 Reponse (réponse générée).
        1. Détection de langue et d'intention
        2. Enregistrement du Message puis de sa Reponse
        3. (Branchement LLM/RAG à venir : réponse de démonstration pour l'instant)
        """
        ConversationService.assert_rate_limit(db, conversation)
        lang = ConversationService.detect_language(user_text)
        intent = ConversationService.detect_intent(user_text)
        now = datetime.utcnow()

        user_msg = Message(
            conversation_id=conversation.idConversation,
            contenu=user_text[:2000],
            dateEnvoi=now,
        )
        db.add(user_msg)
        db.flush()

        if lang == "arabizi":
            reply_text = (
                "Mar7ba bik f SmartCampus AI! L'IIT t9addem Licence Informatique (3 snin), "
                "Cycle Prépa (2 snin) w Génie Logiciel (5 snin). L'ISB t9addem Business Analytics w Finance. "
                "Nnajmou nchoufou chnowa l parcours l'ansab l profil mte3ek!"
            )
        elif lang == "tn":
            reply_text = (
                "مرحباً بك في SmartCampus AI! في الـ IIT فما إجازة في الإعلامية (3 سنوات)، "
                "مرحلة تحضيرية وشهادة مهندس. وفي الـ ISB فما مسارات إدارة أعمال وتحليل بيانات. "
                "تحب نعملو تقييم ونشوفو أما أحسن تكوين يواتيك؟"
            )
        else:
            reply_text = (
                "L'IIT propose 3 grands cursus d'excellence : la Licence Informatique (3 ans), "
                "le Cycle Préparatoire intégré (2 ans) et le Cycle Ingénieur (Génie Logiciel, Télécom, Mécanique). "
                "L'ISB propose quant à elle des cursus en Business Analytics, Finance et Management. "
                "Chaque formation a ses propres conditions d'admission."
            )

        reponse = Reponse(
            message_id=user_msg.idMessage,
            contenu=reply_text,
            date=datetime.utcnow(),
            source=None,
        )
        db.add(reponse)
        conversation.dateDernierModification = reponse.date
        db.commit()
        db.refresh(reponse)

        return MessageResponse(
            message_id=user_msg.idMessage,
            response=reply_text,
            language_detected=lang,
            intent_detected=intent,
            sources=[],
            metadata={"model": "demo"},
            created_at=reponse.date,
        )


conversation_service = ConversationService()
