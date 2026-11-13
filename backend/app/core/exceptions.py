from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Exception de base pour SmartCampus AI conforme au document de spécification.
    Format du corps :
    {
      "error": {
        "code": "AUTH_INVALID_CREDENTIALS",
        "message": "...",
        "details": {...},
        "timestamp": "ISO 8601",
        "request_id": "req_..."
      }
    }
    """
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.headers = headers or {}
        super().__init__(message)


# ==============================================================================
# Exceptions d'Authentification & Rôles
# ==============================================================================
class TokenExpiredException(AppException):
    def __init__(self, message: str = "Le jeton d'accès a expiré"):
        super().__init__(status_code=401, code="AUTH_001", message=message)

class TokenInvalidException(AppException):
    def __init__(self, message: str = "Jeton d'authentification invalide"):
        super().__init__(status_code=401, code="AUTH_002", message=message)

class InsufficientRoleException(AppException):
    def __init__(self, message: str = "Permissions insuffisantes pour cette ressource"):
        super().__init__(status_code=403, code="AUTH_003", message=message)

class InvalidRefreshTokenException(AppException):
    def __init__(self, message: str = "Le jeton de rafraîchissement est invalide ou expiré"):
        super().__init__(status_code=401, code="AUTH_004", message=message)

class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Email ou mot de passe incorrect", field: str = "email"):
        super().__init__(status_code=401, code="AUTH_INVALID_CREDENTIALS", message=message, details={"field": field})


# ==============================================================================
# Exceptions Candidats & Dossiers
# ==============================================================================
class ForbiddenStatusTransitionException(AppException):
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            status_code=409,
            code="CANDIDATE_001",
            message=f"Transition de statut non autorisée depuis '{current_status}' vers '{target_status}'",
            details={"current_status": current_status, "target_status": target_status}
        )

class MissingRGPDConsentException(AppException):
    def __init__(self, message: str = "Le consentement explicite RGPD est obligatoire pour créer une préinscription"):
        super().__init__(status_code=422, code="CANDIDATE_002", message=message, details={"field": "consent_rgpd"})

class CandidateNotAssignedException(AppException):
    def __init__(self, candidate_id: int):
        super().__init__(
            status_code=403,
            code="CANDIDATE_003",
            message="Accès refusé : ce candidat ne vous est pas affecté",
            details={"candidate_id": candidate_id}
        )


# ==============================================================================
# Exceptions IA, RAG & Audio
# ==============================================================================
class RAGServiceUnavailableException(AppException):
    def __init__(self, message: str = "Le service de recherche sémantique RAG est temporairement indisponible"):
        super().__init__(status_code=503, code="RAG_001", message=message)

class NoDocumentFoundException(AppException):
    def __init__(self, query: str):
        super().__init__(
            status_code=404,
            code="RAG_002",
            message="Aucun document trouvé correspondant à votre requête",
            details={"query": query}
        )

class LLMOverloadedException(AppException):
    def __init__(self, message: str = "Le modèle de langage est actuellement saturé. Veuillez réessayer dans 1 minute."):
        super().__init__(status_code=503, code="LLM_001", message=message)

class LLMTimeoutException(AppException):
    def __init__(self, message: str = "Le modèle de langage a dépassé le délai de réponse (> 30s)"):
        super().__init__(status_code=504, code="LLM_002", message=message)

class UnsupportedAudioFormatException(AppException):
    def __init__(self, received_format: str):
        super().__init__(
            status_code=415,
            code="WHISPER_001",
            message="Format audio non supporté. Formats acceptés : wav, mp3, m4a",
            details={"format": received_format, "accepted": ["audio/wav", "audio/mpeg", "audio/m4a"]}
        )

class AudioPayloadTooLargeException(AppException):
    def __init__(self, size_bytes: int, max_bytes: int):
        super().__init__(
            status_code=413,
            code="WHISPER_002",
            message="Fichier audio trop volumineux (durée max : 2 minutes, taille max : 10 Mo)",
            details={"size_bytes": size_bytes, "max_bytes": max_bytes}
        )

class DocumentCorruptedException(AppException):
    def __init__(self, filename: str):
        super().__init__(
            status_code=415,
            code="DOC_001",
            message=f"Le document '{filename}' est corrompu ou illisible. Veuillez le renvoyer.",
            details={"filename": filename}
        )

class DocumentAlreadyIndexedException(AppException):
    def __init__(self, sha256_hash: str):
        super().__init__(
            status_code=409,
            code="DOC_002",
            message="Document déjà indexé (contenu identique détecté via SHA-256)",
            details={"sha256": sha256_hash}
        )

class AssignmentAlreadyProposedException(AppException):
    def __init__(self, candidate_id: int):
        super().__init__(
            status_code=409,
            code="ASSIGN_001",
            message="Une affectation est déjà en cours pour ce candidat. Veuillez la valider ou la refuser.",
            details={"candidate_id": candidate_id}
        )

class TeacherUnavailableException(AppException):
    def __init__(self, teacher_id: int):
        super().__init__(
            status_code=403,
            code="ASSIGN_002",
            message="L'enseignant sélectionné n'est pas disponible pour cette affectation",
            details={"teacher_id": teacher_id}
        )

class RateLimitExceededException(AppException):
    def __init__(self, retry_after: int = 60, limit: int = 30):
        super().__init__(
            status_code=429,
            code="RATE_LIMIT_EXCEEDED",
            message=f"Trop de requêtes. Veuillez réessayer dans {retry_after} secondes.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0"
            }
        )

class ResourceNotFoundException(AppException):
    def __init__(self, resource_name: str, identifier: Any):
        super().__init__(
            status_code=404,
            code=f"{resource_name.upper()}_NOT_FOUND",
            message=f"La ressource {resource_name} ({identifier}) n'a pas été trouvée",
            details={"resource": resource_name, "id": identifier}
        )
