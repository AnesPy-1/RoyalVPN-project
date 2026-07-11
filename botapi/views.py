import base64
import json

from django.contrib.auth import authenticate
from django.db.models import Count, Q, Sum
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.models import CustomUser

from .models import BotPaymentRequest, BotRequestLog, BotSession, WalletTransaction
from .security import get_client_ip, parse_json_body, validate_bot_signature, validate_session_token
from .services import approve_payment_request, create_payment_request, reject_payment_request


def _json_error(code: str, message: str, status: int = 400, extra: dict | None = None) -> JsonResponse:
    payload = {
        "ok": False,
        "error": code,
        "message": message,
    }
    if extra:
        payload.update(extra)
    return JsonResponse(payload, status=status)


def _json_ok(message: str, data: dict | None = None, status: int = 200) -> JsonResponse:
    payload = {"ok": True, "message": message}
    if data:
        payload.update(data)
    return JsonResponse(payload, status=status)


def _record_log(request, status_code: int, user=None, metadata: dict | None = None):
    BotRequestLog.objects.create(
        endpoint=request.path,
        method=request.method,
        ip_address=get_client_ip(request),
        status_code=status_code,
        user=user,
        metadata=metadata or {},
    )


def _require_bot_auth(request):
    ok, error = validate_bot_signature(request)
    if not ok:
        return None, _json_error("auth_failed", error, status=403)
    return True, None


def _require_user_session(request):
    token = request.headers.get("X-Bot-Session", "") or request.headers.get("Authorization", "").removeprefix("BotSession ").strip()
    ok, error, session = validate_session_token(token)
    if not ok:
        return None, _json_error("session_invalid", error, status=401)
    return session, None


@csrf_exempt
@require_POST
def login_view(request):
    auth_ok, error_response = _require_bot_auth(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    body = parse_json_body(request)
    username = body.get("username", "").strip()
    password = body.get("password", "")
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()

    if not username or not password:
        response = _json_error("validation_error", "username and password are required.", status=400)
        _record_log(request, response.status_code)
        return response

    user = authenticate(request, username=username, password=password)
    if not user:
        response = _json_error("invalid_credentials", "The username or password is incorrect.", status=401)
        _record_log(request, response.status_code)
        return response

    token, session = BotSession.issue(user=user, telegram_user_id=telegram_user_id)
    if telegram_user_id and not user.telegram_id:
        user.telegram_id = telegram_user_id
        user.save(update_fields=["telegram_id"])

    response = _json_ok(
        "Login successful.",
        data={
            "session_token": token,
            "expires_at": session.expires_at.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "wallet_balance": user.wallet_balance,
                "date_joined": user.date_joined.isoformat(),
            },
        },
    )
    _record_log(request, response.status_code, user=user)
    return response


@csrf_exempt
@require_GET
def profile_view(request):
    session, error_response = _require_user_session(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    user = session.user
    totals = user.wallet_transactions.aggregate(
        total_top_up=Sum("amount", filter=Q(kind=WalletTransaction.Kind.TOP_UP)),
        total_transactions=Count("id"),
    )
    response = _json_ok(
        "Profile loaded.",
        data={
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "phone": user.phone,
                "telegram_id": user.telegram_id,
                "wallet_balance": user.wallet_balance,
                "date_joined": user.date_joined.isoformat(),
                "total_top_up": totals.get("total_top_up") or 0,
                "total_transactions": totals.get("total_transactions") or 0,
            }
        },
    )
    _record_log(request, response.status_code, user=user)
    return response


@csrf_exempt
@require_POST
def payment_request_view(request):
    session, error_response = _require_user_session(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    body = parse_json_body(request)
    try:
        requested_amount = int(body.get("amount", 0))
    except (TypeError, ValueError):
        response = _json_error("validation_error", "amount must be a positive integer.", status=400)
        _record_log(request, response.status_code, user=session.user)
        return response

    if requested_amount < 1:
        response = _json_error("validation_error", "amount must be a positive integer.", status=400)
        _record_log(request, response.status_code, user=session.user)
        return response

    try:
        payment_request = create_payment_request(user=session.user, requested_amount=requested_amount)
    except ValueError as exc:
        response = _json_error("site_settings_missing", str(exc), status=500)
        _record_log(request, response.status_code, user=session.user)
        return response

    response = _json_ok(
        "Payment request created.",
        data={
            "request": {
                "id": payment_request.id,
                "reference_id": payment_request.reference_id,
                "requested_amount": payment_request.requested_amount,
                "bonus_amount": payment_request.bonus_amount,
                "payable_amount": payment_request.payable_amount,
                "payment_card_number": payment_request.payment_card_number,
                "payment_card_owner": payment_request.payment_card_owner,
                "status": payment_request.status,
                "created_at": payment_request.created_at.isoformat(),
            }
        },
    )
    _record_log(request, response.status_code, user=session.user)
    return response


@csrf_exempt
@require_http_methods(["POST"])
def payment_submit_view(request, request_id: int):
    session, error_response = _require_user_session(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    payment_request = BotPaymentRequest.objects.filter(pk=request_id, user=session.user).first()
    if not payment_request:
        response = _json_error("not_found", "Payment request not found.", status=404)
        _record_log(request, response.status_code, user=session.user)
        return response

    body = parse_json_body(request)
    payment_request.transaction_id = str(body.get("transaction_id", "")).strip()
    payment_request.receipt_text = str(body.get("receipt_text", "")).strip()
    payment_request.receipt_link = str(body.get("receipt_link", "")).strip()
    receipt_image_base64 = str(body.get("receipt_image_base64", "")).strip()
    receipt_image_name = str(body.get("receipt_image_name", "receipt.png")).strip() or "receipt.png"
    if receipt_image_base64:
        try:
            decoded = base64.b64decode(receipt_image_base64)
            payment_request.receipt_image.save(receipt_image_name, ContentFile(decoded), save=False)
        except Exception:
            response = _json_error("validation_error", "receipt_image_base64 is invalid.", status=400)
            _record_log(request, response.status_code, user=session.user)
            return response
    payment_request.save(
        update_fields=[
            "transaction_id",
            "receipt_text",
            "receipt_link",
            "receipt_image",
            "updated_at",
        ]
    )

    response = _json_ok(
        "Receipt submitted.",
        data={
            "request": {
                "id": payment_request.id,
                "reference_id": payment_request.reference_id,
                "user_id": payment_request.user_id,
                "username": payment_request.user.username,
                "requested_amount": payment_request.requested_amount,
                "bonus_amount": payment_request.bonus_amount,
                "payable_amount": payment_request.payable_amount,
                "status": payment_request.status,
                "created_at": payment_request.created_at.isoformat(),
            }
        },
    )
    _record_log(request, response.status_code, user=session.user)
    return response


@csrf_exempt
@require_GET
def admin_statistics_view(request):
    auth_ok, error_response = _require_bot_auth(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    data = {
        "users": {
            "total": CustomUser.objects.count(),
            "with_purchases": CustomUser.objects.filter(wallet_transactions__isnull=False).distinct().count(),
        },
        "payments": {
            "total_requests": BotPaymentRequest.objects.count(),
            "pending": BotPaymentRequest.objects.filter(status=BotPaymentRequest.Status.PENDING).count(),
            "approved": BotPaymentRequest.objects.filter(status=BotPaymentRequest.Status.APPROVED).count(),
            "rejected": BotPaymentRequest.objects.filter(status=BotPaymentRequest.Status.REJECTED).count(),
            "total_amount": WalletTransaction.objects.filter(kind=WalletTransaction.Kind.TOP_UP).aggregate(total=Sum("amount")).get("total") or 0,
        },
    }
    response = _json_ok("Statistics loaded.", data=data)
    _record_log(request, response.status_code)
    return response


@csrf_exempt
@require_GET
def admin_pending_payments_view(request):
    auth_ok, error_response = _require_bot_auth(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    requests = BotPaymentRequest.objects.filter(status=BotPaymentRequest.Status.PENDING).select_related("user")[:20]
    response = _json_ok(
        "Pending payments loaded.",
        data={
            "requests": [
                {
                    "id": item.id,
                    "reference_id": item.reference_id,
                    "username": item.user.username,
                    "amount": item.requested_amount,
                    "bonus_amount": item.bonus_amount,
                    "payable_amount": item.payable_amount,
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                    "receipt_text": item.receipt_text,
                    "receipt_link": item.receipt_link,
                    "transaction_id": item.transaction_id,
                }
                for item in requests
            ]
        },
    )
    _record_log(request, response.status_code)
    return response


@csrf_exempt
@require_POST
def payment_approve_view(request):
    auth_ok, error_response = _require_bot_auth(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    body = parse_json_body(request)
    payment_request_id = body.get("payment_id") or body.get("request_id")
    if not payment_request_id:
        response = _json_error("validation_error", "payment_id is required.", status=400)
        _record_log(request, response.status_code)
        return response

    payment_request = BotPaymentRequest.objects.select_related("user").filter(pk=payment_request_id).first()
    if not payment_request:
        response = _json_error("not_found", "Payment request not found.", status=404)
        _record_log(request, response.status_code)
        return response

    note = str(body.get("note", "")).strip()
    try:
        transaction_obj = approve_payment_request(payment_request=payment_request, note=note)
    except ValueError as exc:
        error_code = str(exc)
        status = 409 if error_code in {"already_approved", "already_rejected"} else 400
        response = _json_error(error_code, "Payment request has already been reviewed.", status=status)
        _record_log(request, response.status_code)
        return response
    response = _json_ok(
        "Payment approved.",
        data={
            "payment": {
                "id": payment_request.id,
                "reference_id": payment_request.reference_id,
                "status": payment_request.status,
                "user_id": payment_request.user_id,
                "username": payment_request.user.username,
                "amount": transaction_obj.amount,
                "new_balance": transaction_obj.new_balance,
            }
        },
    )
    _record_log(request, response.status_code)
    return response


@csrf_exempt
@require_POST
def payment_reject_view(request):
    auth_ok, error_response = _require_bot_auth(request)
    if error_response:
        _record_log(request, error_response.status_code)
        return error_response

    body = parse_json_body(request)
    payment_request_id = body.get("payment_id") or body.get("request_id")
    if not payment_request_id:
        response = _json_error("validation_error", "payment_id is required.", status=400)
        _record_log(request, response.status_code)
        return response

    payment_request = BotPaymentRequest.objects.select_related("user").filter(pk=payment_request_id).first()
    if not payment_request:
        response = _json_error("not_found", "Payment request not found.", status=404)
        _record_log(request, response.status_code)
        return response

    note = str(body.get("note", "")).strip()
    try:
        reject_payment_request(payment_request=payment_request, note=note)
    except ValueError as exc:
        error_code = str(exc)
        status = 409 if error_code in {"already_approved", "already_rejected"} else 400
        response = _json_error(error_code, "Payment request has already been reviewed.", status=status)
        _record_log(request, response.status_code)
        return response
    response = _json_ok(
        "Payment rejected.",
        data={
            "payment": {
                "id": payment_request.id,
                "reference_id": payment_request.reference_id,
                "status": payment_request.status,
                "user_id": payment_request.user_id,
                "username": payment_request.user.username,
            }
        },
    )
    _record_log(request, response.status_code)
    return response
