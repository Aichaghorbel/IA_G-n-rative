"""
Chat conversationnel.

Accès :
* Visiteur SANS compte : libre (session créée automatiquement si aucun jeton n'est fourni) ;
* Candidat : ses conversations (compte) ;
* Enseignant : lecture seule des conversations de ses candidats (rendez-vous commun) ;
* Administrateur : supervision.
Chaque conversation n'est accessible qu'à son propriétaire (voir app/api/ownership.py).
"""
import asyncio
import json
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    Query,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import PaginationQuery, VisitorSession, chat_access, get_db, require_roles
from app.api.ownership import get_candidat_of, get_owned_conversation, get_visiteur_for
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    AudioPayloadTooLargeException,
    InsufficientRoleException,
    ResourceNotFoundException,
    UnsupportedAudioFormatException,
)
from app.core.rbac import Role
from app.core.security import TOKEN_ACCESS, TOKEN_SESSION, decode_token
from app.models.candidate import Candidat
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.conversation import (
    AudioPreferenceRequest,
    ConversationResponse,
    MessageCreate,
    MessageItem,
    MessageResponse,
)
from app.services.conversation_service import conversation_service

router = APIRouter()

CHAT_ROLES = ("Visiteur", "Candidat")


def _to_response(conv: Conversation, with_messages: bool = False) -> ConversationResponse:
    messages: List[MessageItem] = []
    if with_messages:
        messages = _flatten_messages(sorted(conv.messages, key=lambda m: m.idMessage))
    return ConversationResponse(
        conversation_id=conv.idConversation,
        session_id=conv.visiteur.sessionToken if conv.visiteur else None,
        is_anonymous=conv.candidat_id is None,
        messages=messages,
        created_at=conv.dateDernierModification or datetime.utcnow(),
        titre=conv.titre,
    )


def _flatten_messages(messages) -> List[MessageItem]:
    """Message (question) + Reponse (réponse) -> deux éléments chronologiques."""
    items: List[MessageItem] = []
    for m in messages:
        items.append(MessageItem(id=m.idMessage, role="user", content=m.contenu,
                                 created_at=m.dateEnvoi or datetime.utcnow()))
        if m.reponse:
            items.append(MessageItem(id=m.reponse.id, role="assistant", content=m.reponse.contenu,
                                     created_at=m.reponse.date or datetime.utcnow()))
    return items


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ouvrir une nouvelle conversation (accès libre aux visiteurs)",
    description="Sans jeton, une session visiteur est créée automatiquement : récupérez son jeton dans "
                "l'en-tête de réponse `X-Session-Token` et renvoyez-le ensuite.",
)
def create_conversation(
    principal=Depends(chat_access(*CHAT_ROLES)),
    db: Session = Depends(get_db),
):
    role = Role.normalize(principal.role)
    if role == Role.VISITEUR:
        visiteur = get_visiteur_for(db, principal)
        conv = Conversation(visiteur_id=visiteur.id, dateDernierModification=datetime.utcnow())
    elif role == Role.CANDIDAT:
        candidat = get_candidat_of(db, principal)
        if not candidat:
            candidat = Candidat(user_id=principal.id)
            db.add(candidat)
            db.flush()
        conv = Conversation(candidat_id=candidat.id, visiteur_id=candidat.visiteur_id,
                            dateDernierModification=datetime.utcnow())
    else:
        raise InsufficientRoleException("Le chat est réservé aux visiteurs et aux candidats")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _to_response(conv)


@router.get(
    "",
    response_model=List[ConversationResponse],
    summary="Lister mes conversations",
    description="Conversations du candidat connecté ou de la session visiteur courante.",
)
def list_conversations(
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db),
):
    role = Role.normalize(principal.role)
    if role == Role.CANDIDAT:
        candidat = get_candidat_of(db, principal)
        if not candidat:
            return []
        q = db.query(Conversation).filter(Conversation.candidat_id == candidat.id)
    elif role == Role.VISITEUR:
        visiteur = get_visiteur_for(db, principal, create=False)
        if not visiteur:
            return []
        q = db.query(Conversation).filter(
            Conversation.visiteur_id == visiteur.id, Conversation.candidat_id.is_(None)
        )
    else:  # Administrateur : supervision de toutes les conversations
        q = db.query(Conversation)
    return [_to_response(c) for c in q.order_by(Conversation.idConversation.desc()).limit(100).all()]


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Consulter l'état d'une conversation",
)
def get_conversation(
    conversation_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db),
):
    conv = get_owned_conversation(db, conversation_id, principal)
    return _to_response(conv, with_messages=True)


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    summary="Envoyer un message texte",
)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    principal=Depends(chat_access(*CHAT_ROLES)),
    db: Session = Depends(get_db),
):
    conv = get_owned_conversation(db, conversation_id, principal)
    return conversation_service.process_message(db, conv, data.message)


@router.post(
    "/{conversation_id}/audio",
    response_model=MessageResponse,
    summary="Envoyer un message vocal (Audio Whisper)",
    description="Multipart, ≤ 10 Mo, wav/mp3/m4a, transcrit avec Whisper puis traité.",
)
async def send_audio_message(
    conversation_id: int,
    file: UploadFile = File(..., description="Fichier audio wav, mp3 ou m4a"),
    principal=Depends(chat_access(*CHAT_ROLES)),
    db: Session = Depends(get_db),
):
    conv = get_owned_conversation(db, conversation_id, principal)

    allowed_content_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/x-m4a"]
    if file.content_type not in allowed_content_types:
        raise UnsupportedAudioFormatException(file.content_type or "inconnu")

    max_size = settings.MAX_AUDIO_PAYLOAD_BYTES
    content = await file.read(max_size + 1)  # ne charge jamais plus que la limite en mémoire
    if len(content) > max_size:
        raise AudioPayloadTooLargeException(len(content), max_size)

    # Transcription simulée via Whisper (à brancher)
    transcribed_text = "Aslema, n7eb nes2el 3la parcours Licence Informatique fel IIT wa9tech tabda l inscription ?"
    return conversation_service.process_message(db, conv, transcribed_text)


@router.get(
    "/{conversation_id}/messages",
    response_model=List[MessageItem],
    summary="Historique paginé des messages",
    description="Propriétaire, enseignant du candidat (lecture seule) ou administrateur.",
)
def get_messages(
    conversation_id: int,
    pagination: PaginationQuery = Depends(),
    principal=Depends(require_roles("Visiteur", "Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db),
):
    conv = get_owned_conversation(db, conversation_id, principal, staff_read=True)
    rows = (
        db.query(Message).filter(Message.conversation_id == conv.idConversation)
        .order_by(Message.idMessage.asc()).offset(pagination.offset).limit(pagination.limit).all()
    )
    return _flatten_messages(rows)


@router.get(
    "/{conversation_id}/memory",
    summary="Consulter la mémoire conversationnelle",
)
def get_conversation_memory(
    conversation_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db),
):
    conv = get_owned_conversation(db, conversation_id, principal, staff_read=True)
    return {"conversation_id": conv.idConversation, "interets": [], "formations_envisagees": []}


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une conversation (droit à l'effacement RGPD)",
)
def delete_conversation(
    conversation_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat", "Administrateur")),
    db: Session = Depends(get_db),
):
    conv = get_owned_conversation(db, conversation_id, principal)
    db.delete(conv)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/audio-preference",
    summary="Activer ou désactiver la réponse vocale",
)
def set_audio_preference(
    conversation_id: int,
    data: AudioPreferenceRequest,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db),
):
    get_owned_conversation(db, conversation_id, principal)
    # NB : le diagramme de classes ne prévoit pas de colonne « audio » sur Conversation.
    return {"message": "Préférence vocale mise à jour", "audio_enabled": data.audio_enabled}


@router.get(
    "/{conversation_id}/messages/{msg_id}/stream",
    summary="Streaming SSE de la réponse LLM",
)
async def stream_message_sse(
    conversation_id: int,
    msg_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db),
):
    get_owned_conversation(db, conversation_id, principal)

    async def event_generator():
        tokens = [
            "L'IIT ", "propose ", "un cursus ", "d'excellence ", "en Génie Logiciel ",
            "avec ", "un accompagnement ", "personnalisé.",
        ]
        for token in tokens:
            await asyncio.sleep(0.08)
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==============================================================================
# WebSocket : chat temps réel. Accès libre aux visiteurs ; jeton optionnel (?token=...)
# ==============================================================================
WS_MAX_MESSAGE_CHARS = 2000
WS_POLICY_VIOLATION = 1008


def _ws_authenticate(db: Session, token: str | None) -> str:
    """Retourne le rôle de l'appelant ou lève une exception si un jeton est fourni mais invalide."""
    if not token:
        return Role.VISITEUR  # visiteur sans compte : autorisé
    payload = decode_token(token)
    ttype = payload.get("type")
    if ttype == TOKEN_SESSION:
        from app.services.session_service import session_service
        session_service.authenticate(db, token)
        return Role.VISITEUR
    if ttype == TOKEN_ACCESS:
        from app.services.auth_service import auth_service
        if auth_service.is_revoked(db, payload.get("jti")):
            raise AppException(status_code=401, code="AUTH_002", message="Jeton révoqué")
        user = db.get(User, int(payload["sub"]))
        if not user or not user.is_active or payload.get("tv", 0) != (user.token_version or 0):
            raise AppException(status_code=401, code="AUTH_002", message="Jeton invalide")
        return Role.normalize(user.role)
    raise AppException(status_code=401, code="AUTH_002", message="Type de jeton invalide")


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str | None = Query(None)):
    """Streaming temps réel token par token. Un jeton invalide est refusé (1008) ; l'absence de jeton est acceptée."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        try:
            role = _ws_authenticate(db, token)
        except Exception:  # jeton invalide, expiré, révoqué ou mal formé
            await websocket.close(code=WS_POLICY_VIOLATION)
            return
    finally:
        db.close()

    if role not in (Role.VISITEUR, Role.CANDIDAT, Role.ADMINISTRATEUR):
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if len(data) > WS_MAX_MESSAGE_CHARS * 2:
                await websocket.send_text(json.dumps({"error": "Message trop volumineux"}))
                continue
            try:
                req = json.loads(data)
                user_msg = str(req.get("message", ""))[:WS_MAX_MESSAGE_CHARS]
            except (json.JSONDecodeError, AttributeError):
                await websocket.send_text(json.dumps({"error": "Format JSON invalide"}))
                continue
            if not user_msg.strip():
                continue

            response_chunks = [
                "SmartCampus AI : ", "Excellente question ! ",
                "L'IIT et l'ISB offrent des passerelles ", "adaptées à votre niveau.",
            ]
            for chunk in response_chunks:
                await asyncio.sleep(0.05)
                await websocket.send_text(json.dumps({"token": chunk}))
            await websocket.send_text(json.dumps({"done": True}))
    except WebSocketDisconnect:
        pass
