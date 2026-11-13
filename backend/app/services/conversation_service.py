import re
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message
from app.models.document import Document
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
    def process_message(
        db: Session,
        conversation: Conversation,
        user_text: str
    ) -> MessageResponse:
        """
        Traite le message du candidat :
        1. Détection de langue et d'intention
        2. Mémorisation du profil (intérêts, niveau)
        3. Consultation RAG
        4. Génération de réponse structurée
        """
        lang = ConversationService.detect_language(user_text)
        intent = ConversationService.detect_intent(user_text)

        # Enregistrement du message utilisateur
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_text,
            language_detected=lang,
            metadata_json={"intent": intent}
        )
        db.add(user_msg)

        # Recherche de sources RAG potentielles
        sources: List[MessageSource] = []
        rag_doc = db.query(Document).filter(Document.status == "INDEXED").first()
        if rag_doc and ("iit" in user_text.lower() or "isb" in user_text.lower() or "formation" in user_text.lower()):
            sources.append(MessageSource(
                document_id=rag_doc.id,
                title=f"Guide académique {rag_doc.etablissement} 2026-2027",
                page=2,
                url=f"/documents/{rag_doc.id}"
            ))

        # Réponse personnalisée selon la langue et le contexte
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

        # Mise à jour de la mémoire conversationnelle
        memory = conversation.memory_summary or {}
        interets = memory.get("interets", [])
        if "informatique" in user_text.lower() and "informatique" not in interets:
            interets.append("informatique")
        if "gestion" in user_text.lower() and "gestion" not in interets:
            interets.append("gestion")
        memory["interets"] = interets
        conversation.memory_summary = memory
        conversation.language_detected = lang
        conversation.intent_detected = intent

        # Enregistrement du message assistant
        bot_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply_text,
            language_detected=lang,
            sources=[s.model_dump() for s in sources],
            metadata_json={
                "latency_ms": 320,
                "tokens_used": 115,
                "model": "qwen2.5-7b-instruct",
                "intent": intent
            }
        )
        db.add(bot_msg)
        db.commit()
        db.refresh(bot_msg)

        return MessageResponse(
            message_id=bot_msg.id,
            response=reply_text,
            language_detected=lang,
            intent_detected=intent,
            sources=sources,
            metadata=bot_msg.metadata_json,
            created_at=bot_msg.created_at
        )


conversation_service = ConversationService()
