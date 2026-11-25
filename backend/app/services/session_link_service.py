"""
SA-29 — Conserver la conversation d'un visiteur après connexion / création de compte.

Principe
--------
1. Le visiteur chatte avec un jeton de session (X-Session-Token). Ses conversations sont
   rattachées à une ligne `visiteurs` dont `sessionToken` = id de la session.
2. Il crée un compte ou se connecte (jeton d'accès = Authorization: Bearer).
3. Le front renvoie ALORS LES DEUX jetons. Le backend PROPOSE d'associer la session au profil
   candidat (`proposal`) ; rien n'est modifié tant que le candidat n'a pas donné son accord.
4. `link` exécute l'association uniquement si :
     - le candidat a donné son accord explicite (consent=true) ;
     - la session appartient bien à l'appelant : il détient le jeton de session valide
       (signature + hash en base + non expirée) ET l'id fourni correspond à ce jeton ;
     - la session / le visiteur n'est pas déjà lié à un AUTRE candidat.
   Elle est idempotente (rejouer l'appel ne duplique rien) et atomique (une seule transaction,
   session verrouillée en base pendant l'opération).

Aucune nouvelle colonne : on s'appuie sur `visitor_sessions.candidate_id` et
`conversations.candidat_id`, déjà présents.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services.candidate_service import merge_candidats
from app.core.exceptions import (
    AppException,
    SessionAlreadyLinkedException,
    SessionLinkConsentRequiredException,
    SessionOwnershipException,
)
from app.models.candidate import Candidat, Visiteur
from app.models.conversation import Conversation, Message
from app.models.qcm import Preinscription
from app.models.user import User
from app.models.visitor_session import VisitorSession
from app.services.session_service import session_service

logger = logging.getLogger("smartcampus.session_link")

MAX_PREVIEWS = 5
SNIPPET_CHARS = 80


class SessionLinkService:
    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _visiteur_of(db: Session, session: VisitorSession) -> Optional[Visiteur]:
        return db.query(Visiteur).filter(Visiteur.sessionToken == str(session.id)).first()

    @staticmethod
    def _unlinked_conversations(db: Session, visiteur: Optional[Visiteur]) -> List[Conversation]:
        if visiteur is None:
            return []
        return (
            db.query(Conversation)
            .filter(Conversation.visiteur_id == visiteur.id, Conversation.candidat_id.is_(None))
            .order_by(Conversation.idConversation.asc())
            .all()
        )

    @staticmethod
    def _message_counts(db: Session, conv_ids: List[int]) -> Dict[int, int]:
        if not conv_ids:
            return {}
        rows = (
            db.query(Message.conversation_id, func.count(Message.idMessage))
            .filter(Message.conversation_id.in_(conv_ids))
            .group_by(Message.conversation_id)
            .all()
        )
        return {cid: n for cid, n in rows}

    @staticmethod
    def assert_linkable(
        db: Session, candidat: Candidat, session: VisitorSession, visiteur: Optional[Visiteur]
    ) -> None:
        """Refuse (409) si la session ou son visiteur appartient déjà à un autre compte candidat."""
        if session.candidate_id is not None and session.candidate_id != candidat.id:
            other_by_sess = db.get(Candidat, session.candidate_id)
            if other_by_sess and other_by_sess.user_id is not None:
                raise SessionAlreadyLinkedException()
        if visiteur is not None:
            other = (
                db.query(Candidat.id)
                .filter(
                    Candidat.visiteur_id == visiteur.id,
                    Candidat.id != candidat.id,
                    Candidat.user_id.isnot(None),
                )
                .first()
            )
            if other:
                raise SessionAlreadyLinkedException()

    # ------------------------------------------------------------------ proposition
    @staticmethod
    def proposal(db: Session, candidat: Candidat, session: VisitorSession) -> Dict[str, Any]:
        """Décrit ce qui serait associé. Lecture seule : ne modifie rien."""
        base = {"session_id": str(session.id), "consent_required": True}
        visiteur = SessionLinkService._visiteur_of(db, session)

        if session.candidate_id == candidat.id:
            return {**base, "available": False, "already_linked": True,
                    "reason": "Cette session est déjà associée à votre profil"}
        try:
            SessionLinkService.assert_linkable(db, candidat, session, visiteur)
        except AppException as exc:
            return {**base, "available": False, "reason": exc.message}

        convs = SessionLinkService._unlinked_conversations(db, visiteur)
        counts = SessionLinkService._message_counts(db, [c.idConversation for c in convs])
        has_profile = bool(session.profile)
        has_unowned_prereg = False
        if visiteur is not None and visiteur.candidat is not None and visiteur.candidat.user_id is None:
            has_unowned_prereg = (
                db.query(Preinscription.id)
                .filter(Preinscription.candidat_id == visiteur.candidat.id)
                .first()
                is not None
            )

        if not convs and not has_profile and not has_unowned_prereg:
            return {**base, "available": False, "reason": "Aucune conversation à associer"}

        previews = []
        for c in convs[-MAX_PREVIEWS:]:
            first = (
                db.query(Message.contenu)
                .filter(Message.conversation_id == c.idConversation)
                .order_by(Message.idMessage.asc())
                .first()
            )
            previews.append({
                "conversation_id": c.idConversation,
                "titre": c.titre,
                "message_count": counts.get(c.idConversation, 0),
                "first_message": (first[0][:SNIPPET_CHARS] if first else None),
                "last_activity": c.dateDernierModification,
            })
        return {
            **base,
            "available": True,
            "conversations_count": len(convs),
            "messages_count": sum(counts.values()),
            "has_profile_data": has_profile,
            "conversations": previews,
        }

    @staticmethod
    def proposal_for_token(db: Session, user: User, raw_session_token: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Utilisé par /auth/login et /auth/register : ajoute la proposition à la réponse quand un
        X-Session-Token valide accompagne la requête. N'échoue JAMAIS (la connexion prime).
        """
        if not raw_session_token or user.role != "Candidat":
            return None
        try:
            session = session_service.authenticate(db, raw_session_token.strip())
            candidat = db.query(Candidat).filter(Candidat.user_id == user.id).first()
            if candidat is None:
                return None
            data = SessionLinkService.proposal(db, candidat, session)
            return data if data.get("available") else None
        except AppException:
            return None

    # ------------------------------------------------------------------ association
    @staticmethod
    def link(
        db: Session, candidat: Candidat, session: VisitorSession, session_id: str, consent: bool
    ) -> Dict[str, Any]:
        # 1. Accord explicite
        if consent is not True:
            raise SessionLinkConsentRequiredException()

        # 2. Propriété : l'id annoncé doit être celui du jeton de session réellement détenu
        #    (le jeton lui-même a déjà été validé : signature, hash en base, expiration).
        if str(session.id) != str(session_id).strip():
            raise SessionOwnershipException()

        # 3. Verrou de ligne : deux appels simultanés ne peuvent pas lier deux fois
        locked = (
            db.query(VisitorSession).filter(VisitorSession.id == session.id).with_for_update().one()
        )
        visiteur = SessionLinkService._visiteur_of(db, locked)

        # 4. Déjà lié à ce candidat -> idempotent
        if locked.candidate_id == candidat.id:
            db.rollback()
            return {
                "linked": True, "already_linked": True, "candidate_id": candidat.id,
                "session_id": str(locked.id), "conversations_linked": 0, "messages_linked": 0,
                "message": "Cette session était déjà associée à votre profil",
            }

        # 5. Conflits (session ou visiteur appartenant à un autre candidat)
        SessionLinkService.assert_linkable(db, candidat, locked, visiteur)

        # 6. Association (une seule transaction)
        if visiteur is not None:
            unowned_cand = (
                db.query(Candidat)
                .filter(
                    Candidat.visiteur_id == visiteur.id,
                    Candidat.id != candidat.id,
                    Candidat.user_id.is_(None),
                )
                .first()
            )
            if unowned_cand is not None:
                merge_candidats(db, unowned_cand, candidat)

        convs = SessionLinkService._unlinked_conversations(db, visiteur)
        counts = SessionLinkService._message_counts(db, [c.idConversation for c in convs])
        for c in convs:
            c.candidat_id = candidat.id
        if visiteur is not None and candidat.visiteur_id is None:
            candidat.visiteur_id = visiteur.id  # « 1 Visiteur devenir 1 Candidat » (UML)
        locked.candidate_id = candidat.id
        db.commit()

        logger.info(
            "session %s associée au candidat %s (%d conversations)",
            locked.id, candidat.id, len(convs),
        )
        return {
            "linked": True, "already_linked": False, "candidate_id": candidat.id,
            "session_id": str(locked.id), "conversations_linked": len(convs),
            "messages_linked": sum(counts.values()),
            "message": "Votre conversation précédente est maintenant associée à votre profil",
        }


session_link_service = SessionLinkService()
