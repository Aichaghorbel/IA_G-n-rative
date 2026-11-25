from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from app.api.deps import PaginationQuery, require_roles
from app.schemas.admin import (
    AgentDetailStatus,
    AgentSupervisionResponse,
    LogEntryResponse,
    TechMetricsResponse
)

router = APIRouter()


@router.get(
    "/logs",
    response_model=List[LogEntryResponse],
    summary="Journaux système et d'erreurs (Admin)",
    description="Liste paginée des journaux (filtres par niveau, service). Strictement réservé au rôle A (403 pour tout autre rôle)."
)
def get_system_logs(
    response: Response,
    level: Optional[str] = Query(None, description="INFO, WARNING, ERROR"),
    service: Optional[str] = Query(None, description="auth, rag, llm, whisper"),
    pagination: PaginationQuery = Depends(),
    admin=Depends(require_roles("Administrateur"))
):
    now = datetime.now(timezone.utc)
    mock_logs = [
        LogEntryResponse(
            id="log_001",
            timestamp=now,
            level="INFO",
            service="auth",
            message="Connexion réussie pour admin@smartcampus.tn",
            request_id="req_987abc"
        ),
        LogEntryResponse(
            id="log_002",
            timestamp=now,
            level="INFO",
            service="llm",
            message="Génération de réponse en langue 'arabizi' réussie (latence: 320ms, tokens: 115)",
            request_id="req_abc123"
        ),
        LogEntryResponse(
            id="log_003",
            timestamp=now,
            level="INFO",
            service="rag",
            message="Recherche sémantique exécutée avec 3 sources indexées",
            request_id="req_def456"
        )
    ]

    if level and isinstance(level, str):
        mock_logs = [l for l in mock_logs if l.level == level]
    if service and isinstance(service, str):
        mock_logs = [l for l in mock_logs if l.service == service]

    response.headers["X-Total-Count"] = str(len(mock_logs))
    return mock_logs


@router.get(
    "/agents/status",
    response_model=AgentSupervisionResponse,
    summary="Supervision des agents IA (Admin)",
    description="Statut des agents IA (LLM, RAG, Whisper) : disponibilité, latence et file d'attente."
)
def get_agents_status(
    admin=Depends(require_roles("Administrateur"))
):
    now = datetime.now(timezone.utc)
    return AgentSupervisionResponse(
        llm=AgentDetailStatus(
            status="healthy",
            latency_ms=340.0,
            queue_length=0,
            model_name="qwen2.5-7b-instruct"
        ),
        rag=AgentDetailStatus(
            status="healthy",
            latency_ms=45.0,
            queue_length=0,
            model_name="pgvector / bge-m3"
        ),
        whisper=AgentDetailStatus(
            status="healthy",
            latency_ms=510.0,
            queue_length=1,
            model_name="whisper-base-multilingual"
        ),
        timestamp=now
    )


@router.get(
    "/metrics",
    response_model=TechMetricsResponse,
    summary="Métriques techniques de la plateforme (Admin)",
    description="Métriques techniques en direct : CPU, RAM, requêtes par minute et sessions actives."
)
def get_technical_metrics(
    admin=Depends(require_roles("Administrateur"))
):
    return TechMetricsResponse(
        cpu_percent=14.5,
        ram_percent=42.0,
        requests_per_minute=58,
        active_sessions=12,
        uptime_seconds=86400
    )
