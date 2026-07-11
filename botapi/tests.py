import hashlib
import hmac
import json
import secrets
import time

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import SiteSettings

from .models import BotPaymentRequest, BotSession


@override_settings(BOT_API_KEY="test-key", BOT_API_SECRET="test-secret")
class BotApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username="alice",
            password="password123",
            wallet_balance=0,
        )
        SiteSettings.objects.create(
            site_name1="Royal",
            site_name2="VPN",
            site_logo="logo.png",
            payment_card="6037997512345678",
            payment_card_name="RoyalVPN",
            up_time="99.9",
            countries_count="10",
            servers_count="25",
            footer_text="RoyalVPN",
            users_count_for_about_us="1000",
            established_year_for_about_us="2024",
            feature1_for_about_us="Fast",
            feature2_for_about_us="Safe",
            feature3_for_about_us="Private",
            feature4_for_about_us="Stable",
            telegram_support_id_link="https://t.me/support",
            telegram_Channel_id_link="https://t.me/channel",
            telegram_bot_id_link="https://t.me/bot",
        )

    def _signed_headers(self, method: str, path: str, body: bytes):
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        body_hash = hashlib.sha256(body).hexdigest()
        canonical = f"{timestamp}.{nonce}.{method}.{path}.{body_hash}".encode("utf-8")
        signature = hmac.new(b"test-secret", canonical, hashlib.sha256).hexdigest()
        return {
            "HTTP_X_BOT_API_KEY": "test-key",
            "HTTP_X_BOT_TIMESTAMP": timestamp,
            "HTTP_X_BOT_NONCE": nonce,
            "HTTP_X_BOT_SIGNATURE": signature,
            "content_type": "application/json",
        }

    def test_login_creates_bot_session(self):
        body = json.dumps(
            {
                "username": "alice",
                "password": "password123",
                "telegram_user_id": "12345",
            },
            separators=(",", ":"),
        ).encode("utf-8")
        response = self.client.post(
            reverse("bot-login"),
            data=body,
            **self._signed_headers("POST", reverse("bot-login"), body),
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertIn("session_token", payload)
        self.assertEqual(payload["user"]["wallet_balance"], 0)
        self.assertTrue(BotSession.objects.exists())

    def test_payment_request_increments_with_bonus_snapshot(self):
        login_body = json.dumps(
            {
                "username": "alice",
                "password": "password123",
                "telegram_user_id": "12345",
            },
            separators=(",", ":"),
        ).encode("utf-8")
        login_response = self.client.post(
            reverse("bot-login"),
            data=login_body,
            **self._signed_headers("POST", reverse("bot-login"), login_body),
        )
        session_token = login_response.json()["session_token"]

        body = json.dumps({"amount": 500000}, separators=(",", ":")).encode("utf-8")
        response = self.client.post(
            reverse("bot-payment-request"),
            data=body,
            **{
                **self._signed_headers("POST", reverse("bot-payment-request"), body),
                "HTTP_X_BOT_SESSION": session_token,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        payment_request = BotPaymentRequest.objects.get(pk=payload["request"]["id"])
        self.assertEqual(payment_request.payment_card_number, "6037997512345678")
        self.assertGreaterEqual(payment_request.bonus_amount, 200)
        self.assertLessEqual(payment_request.bonus_amount, 999)
