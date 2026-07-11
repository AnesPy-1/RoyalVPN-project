import hashlib
import hmac
import json

from django.conf import settings
from django.core.cache import cache


def _get_allowed_ips() -> set[str]:
    raw = getattr(settings, "BOT_ALLOWED_IPS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _canonical_payload(request) -> bytes:
    body = request.body or b""
    body_hash = hashlib.sha256(body).hexdigest()
    timestamp = request.headers.get("X-Bot-Timestamp", "")
    nonce = request.headers.get("X-Bot-Nonce", "")
    method = request.method.upper()
    path = request.path
    canonical = f"{timestamp}.{nonce}.{method}.{path}.{body_hash}"
    return canonical.encode("utf-8")


def validate_bot_signature(request) -> tuple[bool, str]:
    api_key = request.headers.get("X-Bot-API-Key", "")
    timestamp = request.headers.get("X-Bot-Timestamp", "")
    nonce = request.headers.get("X-Bot-Nonce", "")
    signature = request.headers.get("X-Bot-Signature", "")
    configured_key = getattr(settings, "BOT_API_KEY", "")
    configured_secret = getattr(settings, "BOT_API_SECRET", "")

    if not configured_key or not configured_secret:
        return False, "bot_api_not_configured"

    if not api_key or not timestamp or not nonce or not signature:
        return False, "missing_bot_headers"

    if api_key != configured_key:
        return False, "invalid_api_key"

    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return False, "invalid_timestamp"

    window = int(getattr(settings, "BOT_SIGNATURE_WINDOW_SECONDS", 300))
    now = int(__import__("time").time())
    if abs(now - timestamp_int) > window:
        return False, "timestamp_expired"

    nonce_key = f"bot-nonce:{nonce}"
    if not cache.add(nonce_key, 1, timeout=window):
        return False, "replayed_nonce"

    expected = hmac.new(
        configured_secret.encode("utf-8"),
        _canonical_payload(request),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False, "invalid_signature"

    allowed_ips = _get_allowed_ips()
    if allowed_ips:
        client_ip = get_client_ip(request)
        if client_ip not in allowed_ips:
            return False, "ip_not_allowed"

    return True, ""


def validate_session_token(token: str) -> tuple[bool, str, object]:
    if not token:
        return False, "missing_session_token", None

    from .models import BotSession

    token_hash = BotSession.hash_token(token)
    session = BotSession.objects.select_related("user").filter(
        token_hash=token_hash,
        is_active=True,
    ).first()
    if not session:
        return False, "invalid_session", None
    if session.is_expired():
        session.is_active = False
        session.save(update_fields=["is_active"])
        return False, "session_expired", None
    return True, "", session


def parse_json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}
