import random
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from core.models import SiteSettings

from .models import BotPaymentRequest, WalletTransaction


@dataclass
class PaymentRequestSnapshot:
    card_number: str
    card_owner: str
    bonus_amount: int
    payable_amount: int


def create_payment_request(*, user, requested_amount: int) -> BotPaymentRequest:
    site_settings = SiteSettings.objects.first()
    if not site_settings:
        raise ValueError("site_settings_missing")

    bonus_amount = random.randint(200, 999)
    payable_amount = requested_amount + bonus_amount
    return BotPaymentRequest.objects.create(
        user=user,
        reference_id=BotPaymentRequest.generate_reference_id(),
        requested_amount=requested_amount,
        bonus_amount=bonus_amount,
        payable_amount=payable_amount,
        payment_card_number=site_settings.payment_card,
        payment_card_owner=site_settings.payment_card_name,
    )


@transaction.atomic
def approve_payment_request(*, payment_request: BotPaymentRequest, approved_by=None, note: str = "") -> WalletTransaction:
    payment_request = BotPaymentRequest.objects.select_for_update().select_related("user").get(pk=payment_request.pk)
    if payment_request.status == BotPaymentRequest.Status.APPROVED:
        raise ValueError("already_approved")
    if payment_request.status == BotPaymentRequest.Status.REJECTED:
        raise ValueError("already_rejected")

    user_model = payment_request.user.__class__
    user = user_model.objects.select_for_update().get(pk=payment_request.user_id)
    previous_balance = int(user.wallet_balance)
    new_balance = previous_balance + int(payment_request.payable_amount)
    user.wallet_balance = new_balance
    user.save(update_fields=["wallet_balance"])

    transaction_obj = WalletTransaction.objects.create(
        user=user,
        kind=WalletTransaction.Kind.TOP_UP,
        amount=payment_request.payable_amount,
        previous_balance=previous_balance,
        new_balance=new_balance,
        reference_code=payment_request.reference_id,
        note=note or payment_request.admin_note,
        request=payment_request,
        created_by=approved_by,
    )

    payment_request.status = BotPaymentRequest.Status.APPROVED
    payment_request.reviewed_by = approved_by
    payment_request.reviewed_at = timezone.now()
    payment_request.admin_note = note or payment_request.admin_note
    payment_request.approved_transaction = transaction_obj
    payment_request.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "admin_note",
            "approved_transaction",
            "updated_at",
        ]
    )
    return transaction_obj


def reject_payment_request(*, payment_request: BotPaymentRequest, approved_by=None, note: str = "") -> BotPaymentRequest:
    if payment_request.status == BotPaymentRequest.Status.APPROVED:
        raise ValueError("already_approved")
    payment_request.status = BotPaymentRequest.Status.REJECTED
    payment_request.reviewed_by = approved_by
    payment_request.reviewed_at = timezone.now()
    payment_request.admin_note = note or payment_request.admin_note
    payment_request.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "admin_note",
            "updated_at",
        ]
    )
    return payment_request
