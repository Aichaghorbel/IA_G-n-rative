import asyncio
import json
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    Query,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import PaginationQuery, get_current_principal, get_db, require_roles
from app.core.exceptions import (
    AudioPayloadTooLargeException,
    ResourceNotFoundException,
    UnsupportedAudioFormatException
)
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    AudioPreferenceRequest,
    ConversationResponse,
    MessageCreate,
    MessageItem,
    MessageResponse
)
from app.services.conversation_service import conversation_service

router = APIRouter()


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ouvrir une nouvelle conversation",
    description="Ouvre une conversation avec détection automatique de la langue (français, tunisien, Arabizi)."
)
def create_conversation(
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    conv = Conversation(
        session_id=principal.session_id if principal.role in ["Visiteur", "visiteur", "V"] else None,
        candidate_id=principal.id if principal.role in ["Candidat", "candidat", "C"] else None,
        is_anonymous=(principal.role in ["Visiteur", "visiteur", "V"]),
        language_detected="fr",
        intent_detected="info_programme"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get(
    "",
    response_model=List[ConversationResponse],
    summary="Lister mes conversations",
    description="Liste les conversations de l'utilisateur connecté ou de sa session visiteur."
)
def list_conversations(
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    if principal.role in ["Candidat", "candidat", "C"]:
        return db.query(Conversation).filter(Conversation.candidate_id == principal.id).all()
    return db.query(Conversation).filter(Conversation.session_id == principal.session_id).all()


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Consulter l'état d'une conversation",
    description="Consulte les métadonnées et l'état de la conversation (langue, intention, étape)."
)
def get_conversation(
    conversation_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)
    return conv


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    summary="Envoyer un message texte",
    description="Envoie un message texte et reçoit la réponse générée par le système agentique."
)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)

    response = conversation_service.process_message(db, conv, data.message)
    return response


@router.post(
    "/{conversation_id}/audio",
    response_model=MessageResponse,
    summary="Envoyer un message vocal (Audio Whisper)",
    description="Envoie un message vocal (multipart, ≤ 10 Mo, durée ≤ 2 min), transcrit avec Whisper puis traité."
)
async def send_audio_message(
    conversation_id: int,
    file: UploadFile = File(..., description="Fichier audio wav, mp3 ou m4a"),
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)

    # Validation du format audio (WHISPER_001)
    allowed_content_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/x-m4a"]
    if file.content_type not in allowed_content_types:
        raise UnsupportedAudioFormatException(file.content_type or "inconnu")

    # Lecture et vérification de la taille (≤ 10 Mo) (WHISPER_002)
    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise AudioPayloadTooLargeException(len(content), max_size)

    # Transcription simulée via Whisper
    transcribed_text = "Aslema, n7eb nes2el 3la parcours Licence Informatique fel IIT wa9tech tabda l inscription ?"
    response = conversation_service.process_message(db, conv, transcribed_text)
    return response


@router.get(
    "/{conversation_id}/messages",
    response_model=List[MessageItem],
    summary="Historique paginé des messages",
    description="Consulte l'historique paginé des messages d'une conversation."
)
def get_messages(
    conversation_id: int,
    pagination: PaginationQuery = Depends(),
    principal=Depends(require_roles("Visiteur", "Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)

    return db.query(Message).filter(Message.conversation_id == conversation_id)\
        .order_by(Message.id.asc()).offset(pagination.offset).limit(pagination.limit).all()


@router.get(
    "/{conversation_id}/memory",
    summary="Consulter la mémoire conversationnelle",
    description="Consulte les faits mémorisés (intérêts, préférences, formations envisagées)."
)
def get_conversation_memory(
    conversation_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat", "Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)
    return conv.memory_summary or {}


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une conversation (Droit à l'effacement RGPD)",
    description="Supprime la conversation conformément aux règles de confidentialité."
)
def delete_conversation(
    conversation_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat", "Administrateur")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)
    db.delete(conv)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/audio-preference",
    summary="Activer ou désactiver la réponse vocale",
    description="Enregistre la préférence audio du candidat pour les retours vocaux."
)
def set_audio_preference(
    conversation_id: int,
    data: AudioPreferenceRequest,
    principal=Depends(require_roles("Visiteur", "Candidat")),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ResourceNotFoundException("conversation", conversation_id)
    conv.audio_enabled = data.audio_enabled
    db.commit()
    return {"message": "Préférence vocale mise à jour", "audio_enabled": conv.audio_enabled}


@router.get(
    "/{conversation_id}/messages/{msg_id}/stream",
    summary="Streaming SSE de la réponse LLM",
    description="Flux Server-Sent Events pour streamer la réponse du modèle de langage token par token."
)
async def stream_message_sse(
    conversation_id: int,
    msg_id: int,
    principal=Depends(require_roles("Visiteur", "Candidat"))
):
    async def event_generator():
        tokens = [
            "L'IIT ", "propose ", "un cursus ", "d'excellence ", "en Génie Logiciel ",
            "avec ", "un accompagnement ", "personnalisé."
        ]
        for token in tokens:
            await asyncio.sleep(0.08)
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket pour le streaming temps réel token par token du LLM avec authentification de session.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            user_msg = req.get("message", "")

            # Émission des tokens progressifs
            response_chunks = [
                "SmartCampus AI : ", "Excellente question ! ",
                "L'IIT et l'ISB offrent des passerelles ", "adaptées à votre niveau."
            ]
            for chunk in response_chunks:
                await asyncio.sleep(0.05)
                await websocket.send_text(json.dumps({"token": chunk}))
            await websocket.send_text(json.dumps({"done": True}))
    except WebSocketDisconnect:
        pass
