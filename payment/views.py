from django.contrib import messages
from django.utils.text import gettext_lazy as _
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from orders.models import Order
from payment.models import Payment


@login_required
def payment_creation_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.status != Order.OrderStatus.PENDING_PAYMENT:
        messages.warning(request, _("این سفارش قبلا پرداخت شده یا دیگر قابل پرداخت نیست."))
        return redirect("home")

    wallet_balance = request.user.wallet_balance
    shortage_amount = 0

    if request.method == "POST":
        if wallet_balance >= order.final_price:
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                total_price=order.final_price,
            )
            order.status = Order.OrderStatus.PAID
            order.save(update_fields=["status"])
            request.user.wallet_balance = wallet_balance - order.final_price
            request.user.save(update_fields=["wallet_balance"])
            messages.success(request, _(
                "پرداخت سفارش با استفاده از کیف پول شما انجام شد. سفارش در حال تحویل است."
            ))
            return redirect('get-sub', order.id, payment.id)

        shortage_amount = order.final_price - wallet_balance
        messages.error(
            request,
            _(
                "موجودی کیف پول شما کافی نیست. شما %(shortage)s تومان کسری دارید و باید %(required)s تومان شارژ کنید."
            ) % {
                'shortage': f"{shortage_amount:,}",
                'required': f"{order.final_price:,}",
            },
        )

    return render(
        request,
        'payment/payment.html',
        context={
            'order': order,
            'wallet_balance': wallet_balance,
            'shortage_amount': shortage_amount,
        },
    )
