"""
Autorisation au niveau de la ressource (« qui possède quoi ») :
un rôle autorisé ne suffit pas, il faut aussi être le propriétaire (ou le personnel habilité).

* Visiteur     -> ses propres conversations (via sa session)
* Candidat     -> ses conversations (compte) + celles de sa session visiteur d'origine
* Enseignant   -> lecture seule des candidats avec lesquels il a un rendez-vous
* Administrateur -> accès transverse
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.api.deps import Principal, VisitorSession
from app.core.exceptions import (
    CandidateNotAssignedException,
    InsufficientRoleException,
    ResourceNotFoundException,
)
from app.core.rbac import Role
from app.models.appointment import RendezVous
from app.models.candidate import Candidat, Visiteur
from app.models.conversation import Conversation
from app.models.user import User


def get_candidat_of(db: Session, user: User) -> Optional[Candidat]:
    return db.query(Candidat).filter(Candidat.user_id == user.id).first()


def get_visiteur_for(db: Session, principal: VisitorSession, create: bool = True) -> Optional[Visiteur]:
    """Retrouve (ou crée) la ligne `visiteurs` associée à la session du visiteur."""
    if not principal.session_id:
        return None
    visiteur = db.query(Visiteur).filter(Visiteur.sessionToken == principal.session_id).first()
    if visiteur is None and create:
        visiteur = Visiteur(sessionToken=principal.session_id, dateVisite=date.today())
        db.add(visiteur)
        db.flush()
    return visiteur


def teacher_has_access_to(db: Session, teacher_id: int, candidat_id: int) -> bool:
    """Un enseignant n'accède qu'aux candidats avec lesquels il a (ou a eu) un rendez-vous."""
    return (
        db.query(RendezVous.id)
        .filter(RendezVous.enseignant_id == teacher_id, RendezVous.candidat_id == candidat_id)
        .first()
        is not None
    )


def assert_teacher_access(db: Session, teacher: User, candidat: Candidat) -> None:
    if not teacher_has_access_to(db, teacher.id, candidat.id):
        raise CandidateNotAssignedException(candidat.id)


def get_owned_conversation(
    db: Session, conversation_id: int, principal: Principal, *, staff_read: bool = False
) -> Conversation:
    """
    Charge une conversation en vérifiant que l'appelant y a droit.
    Renvoie 404 (et non 403) si elle appartient à quelqu'un d'autre : on ne révèle pas
    l'existence des conversations des autres.
    `staff_read=True` autorise la lecture à l'enseignant concerné.
    """
    conv = db.query(Conversation).filter(Conversation.idConversation == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)

    role = Role.normalize(principal.role)

    if role == Role.ADMINISTRATEUR:
        return conv

    if role == Role.VISITEUR:
        visiteur = get_visiteur_for(db, principal, create=False)
        if visiteur and conv.visiteur_id == visiteur.id and conv.candidat_id is None:
            return conv
        raise ResourceNotFoundException("conversation", conversation_id)

    if role == Role.CANDIDAT:
        candidat = get_candidat_of(db, principal)
        if candidat and (
            conv.candidat_id == candidat.id
            or (candidat.visiteur_id is not None and conv.visiteur_id == candidat.visiteur_id)
        ):
            return conv
        raise ResourceNotFoundException("conversation", conversation_id)

    if role == Role.ENSEIGNANT and staff_read:
        if conv.candidat_id and teacher_has_access_to(db, principal.id, conv.candidat_id):
            return conv
        raise ResourceNotFoundException("conversation", conversation_id)

    raise InsufficientRoleException()


def assert_can_access_candidat(
    db: Session, principal: Principal, candidat_id: int, *, resource: str = "ressource", resource_id=None
) -> None:
    """
    Contrôle d'accès aux données d'un candidat (recommandations, préinscriptions, QCM...).
    Administrateur : tout. Candidat : uniquement les siennes. Enseignant : ses candidats.
    Visiteur : uniquement les ressources rattachées à sa session visiteur.
    Refus -> 404 (n'indique pas si la ressource d'un tiers existe).
    """
    role = Role.normalize(principal.role)
    if role == Role.ADMINISTRATEUR:
        return
    if role == Role.VISITEUR:
        visiteur = get_visiteur_for(db, principal, create=False)
        if visiteur and visiteur.candidat and visiteur.candidat.id == candidat_id:
            return
    elif role == Role.CANDIDAT:
        own = get_candidat_of(db, principal)
        if own and own.id == candidat_id:
            return
    elif role == Role.ENSEIGNANT:
        if teacher_has_access_to(db, principal.id, candidat_id):
            return
    raise ResourceNotFoundException(resource, resource_id if resource_id is not None else candidat_id)
