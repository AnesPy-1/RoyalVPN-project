from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from orders.models import Order
from payment.forms import PaymentForm


def payment_creation_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.status != Order.OrderStatus.PENDING_PAYMENT:
        messages.warning(request, "این سفارش قبلاً پرداخت شده یا دیگر قابل پرداخت نیست.")
        return redirect("home")

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.order = order
            obj.user = request.user
            obj.total_price = order.final_price
            obj.save()
            order.status = Order.OrderStatus.PAID
            order.save()
            messages.success(request, "پرداخت با موفقیت انجام شد.")
            return redirect('get-sub', order.id, obj.id)

        messages.error(request, "لطفا اطلاعات را به درستی وارد نمایید.")
    else:
        form = PaymentForm()
    return render(request, 'payment/payment.html', context={'form':form, 'order':order})