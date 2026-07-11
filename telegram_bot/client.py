import hashlib
import hmac
import base64
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from .config import BOT_API_BASE_URL, BOT_API_KEY, BOT_API_SECRET, BOT_REQUEST_TIMEOUT


@dataclass
class BotAPIError(Exception):
    message: str
    status_code: int | None = None
    code: str | None = None


class RoyalVPNBotClient:
    def __init__(self):
        self.session = requests.Session()

    def _signed_headers(self, method: str, path: str, body: bytes) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        body_hash = hashlib.sha256(body).hexdigest()
        canonical = f"{timestamp}.{nonce}.{method.upper()}.{path}.{body_hash}".encode("utf-8")
        signature = hmac.new(BOT_API_SECRET.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
        return {
            "X-Bot-API-Key": BOT_API_KEY,
            "X-Bot-Timestamp": timestamp,
            "X-Bot-Nonce": nonce,
            "X-Bot-Signature": signature,
            "Content-Type": "application/json",
        }

    def _request_json(self, method: str, path: str, payload: dict | None = None, session_token: str | None = None):
        url = f"{BOT_API_BASE_URL}{path}"
        body = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = self._signed_headers(method, urlparse(url).path, body)
        if session_token:
            headers["X-Bot-Session"] = session_token
        response = self.session.request(
            method=method,
            url=url,
            data=body,
            headers=headers,
            timeout=BOT_REQUEST_TIMEOUT,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise BotAPIError("The server returned an invalid response.", response.status_code) from exc
        if not response.ok or not data.get("ok"):
            raise BotAPIError(
                data.get("message", "Request failed."),
                response.status_code,
                data.get("error"),
            )
        return data

    def login(self, username: str, password: str, telegram_user_id: str):
        return self._request_json(
            "POST",
            "/login/",
            payload={
                "username": username,
                "password": password,
                "telegram_user_id": telegram_user_id,
            },
        )

    def profile(self, session_token: str):
        return self._request_json("GET", "/profile/", session_token=session_token)

    def create_payment_request(self, session_token: str, amount: int):
        return self._request_json(
            "POST",
            "/payment/request/",
            payload={"amount": amount},
            session_token=session_token,
        )

    def submit_receipt(self, session_token: str, request_id: int, *, receipt_text: str = "", receipt_link: str = "", transaction_id: str = "", receipt_image_path: str | None = None):
        url = f"{BOT_API_BASE_URL}/payment/{request_id}/submit/"
        payload = {
            "receipt_text": receipt_text,
            "receipt_link": receipt_link,
            "transaction_id": transaction_id,
        }
        if receipt_image_path:
            with open(receipt_image_path, "rb") as receipt_file:
                payload["receipt_image_base64"] = base64.b64encode(receipt_file.read()).decode("ascii")
                payload["receipt_image_name"] = receipt_image_path.split("\\")[-1].split("/")[-1]
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = self._signed_headers("POST", urlparse(url).path, body)
        headers["X-Bot-Session"] = session_token
        response = self.session.post(url, headers=headers, data=body, timeout=BOT_REQUEST_TIMEOUT)

        try:
            result = response.json()
        except ValueError as exc:
            raise BotAPIError("The server returned an invalid response.", response.status_code) from exc
        if not response.ok or not result.get("ok"):
            raise BotAPIError(
                result.get("message", "Receipt submission failed."),
                response.status_code,
                result.get("error"),
            )
        return result

    def admin_statistics(self):
        return self._request_json("GET", "/admin/statistics/")

    def admin_pending_payments(self):
        return self._request_json("GET", "/admin/pending-payments/")

    def approve_payment(self, payment_id: int, note: str = ""):
        return self._request_json("POST", "/payment/approve/", payload={"payment_id": payment_id, "note": note})

    def reject_payment(self, payment_id: int, note: str = ""):
        return self._request_json("POST", "/payment/reject/", payload={"payment_id": payment_id, "note": note})
