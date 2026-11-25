"""
Vérification d'identité par code OTP envoyé par e-mail.

Garanties :
- code à 6 chiffres généré avec `secrets` (CSPRNG) ;
- stocké haché (HMAC) — jamais en clair ;
- expiration (OTP_TTL_SECONDS), usage unique, nombre d'essais limité,
  délai minimal entre deux envois.

Le stockage est en mémoire (processus unique, dev/démo). Pour plusieurs workers,
remplacer `_store` par Redis (REDIS_URL est déjà configuré) en gardant la même interface.
"""
import hashlib
import hmac
import logging
import secrets
import smtplib
import threading
import time
from email.message import EmailMessage
from typing import Dict, Optional

from app.core.config import settings
from app.core.exceptions import (
    OTPInvalidException,
    OTPTooManyAttemptsException,
    RateLimitExceededException,
)

logger = logging.getLogger("smartcampus.otp")


class _Entry:
    __slots__ = ("code_hash", "expires_at", "attempts", "sent_at")

    def __init__(self, code_hash: str, expires_at: float, sent_at: float):
        self.code_hash = code_hash
        self.expires_at = expires_at
        self.attempts = 0
        self.sent_at = sent_at


class OTPService:
    def __init__(self) -> None:
        self._store: Dict[str, _Entry] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _hash(email: str, code: str) -> str:
        msg = f"{email.lower()}:{code}".encode()
        return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()

    def _purge(self, now: float) -> None:
        for k in [k for k, e in self._store.items() if e.expires_at < now]:
            del self._store[k]

    def request(self, email: str) -> str:
        """Génère et mémorise un OTP. Retourne le code (à envoyer par e-mail)."""
        email = email.lower()
        now = time.time()
        with self._lock:
            self._purge(now)
            existing = self._store.get(email)
            if existing and now - existing.sent_at < settings.OTP_RESEND_COOLDOWN_SECONDS:
                wait = int(settings.OTP_RESEND_COOLDOWN_SECONDS - (now - existing.sent_at)) + 1
                raise RateLimitExceededException(retry_after=wait, limit=1)
            code = f"{secrets.randbelow(1_000_000):06d}"
            self._store[email] = _Entry(
                self._hash(email, code), now + settings.OTP_TTL_SECONDS, now
            )
        return code

    def verify(self, email: str, code: str) -> None:
        """Valide l'OTP (usage unique). Lève OTPInvalidException / OTPTooManyAttemptsException."""
        email = email.lower()
        now = time.time()
        with self._lock:
            entry = self._store.get(email)
            if not entry or entry.expires_at < now:
                self._store.pop(email, None)
                raise OTPInvalidException()
            if entry.attempts >= settings.OTP_MAX_ATTEMPTS:
                self._store.pop(email, None)
                raise OTPTooManyAttemptsException()
            entry.attempts += 1
            if not hmac.compare_digest(entry.code_hash, self._hash(email, code)):
                if entry.attempts >= settings.OTP_MAX_ATTEMPTS:
                    self._store.pop(email, None)
                    raise OTPTooManyAttemptsException()
                raise OTPInvalidException()
            del self._store[email]  # usage unique

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @staticmethod
    def send_email(email: str, code: str) -> bool:
        """Envoi SMTP best-effort (Mailpit en local). Retourne False si l'envoi échoue."""
        msg = EmailMessage()
        msg["Subject"] = "SmartCampus — votre code de vérification"
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = email
        msg.set_content(
            f"Votre code de vérification SmartCampus est : {code}\n"
            f"Il expire dans {settings.OTP_TTL_SECONDS // 60} minutes. "
            "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message."
        )
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as smtp:
                if settings.SMTP_USER:
                    smtp.starttls()
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(msg)
            return True
        except Exception as exc:  # SMTP indisponible : ne casse pas le flux
            logger.warning("Envoi OTP impossible (%s)", type(exc).__name__)
            return False


otp_service = OTPService()
