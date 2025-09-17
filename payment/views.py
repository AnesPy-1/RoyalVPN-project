from django.contrib import messages
from django.utils.text import gettext_lazy as _
from django.shortcuts import render, get_object_or_404, redirect

from orders.models import Order
from payment.forms import PaymentForm


def payment_creation_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.status != Order.OrderStatus.PENDING_PAYMENT:
        messages.warning(request,  _("This order has already been paid or is no longer payable."))
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
            messages.success(request, _("Payment was successful."))
            return redirect('get-sub', order.id, obj.id)

        messages.error(request, _("Please enter the information correctly."))
    else:
        form = PaymentForm()
    return render(request, 'payment/payment.html', context={'form':form, 'order':order})
