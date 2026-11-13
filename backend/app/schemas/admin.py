from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LogEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR
    service: str  # auth, rag, llm, whisper, appointment
    message: str
    request_id: Optional[str] = None


class AgentDetailStatus(BaseModel):
    status: str  # healthy, degraded, unavailable
    latency_ms: float
    queue_length: int
    model_name: str


class AgentSupervisionResponse(BaseModel):
    llm: AgentDetailStatus
    rag: AgentDetailStatus
    whisper: AgentDetailStatus
    timestamp: datetime


class TechMetricsResponse(BaseModel):
    cpu_percent: float
    ram_percent: float
    requests_per_minute: int
    active_sessions: int
    uptime_seconds: int
