from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils.text import gettext_lazy as gt_lazy

from cart.models import Cart, CartItem
from .forms import OrderCreationForm
from .models import Order, OrderItem


@login_required
def order_delete_view(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.status == Order.OrderStatus.PAID:
        messages.warning(request, gt_lazy("سفارش پرداخت شده را نمی‌توانید حذف کنید."))
        return redirect('dashboard')

    if request.method == 'POST':
        order.delete()
        messages.success(request, gt_lazy("سفارش شما حذف شد."))
        return redirect('dashboard')

    return redirect('dashboard')


@login_required
def order_create_view(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    if not cart.items.all():
        return redirect('pricing')

    if request.method == 'POST':
        form = OrderCreationForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.name = request.user.username
            obj.phone_number = request.user.phone or ""
            if not obj.telegram_id:
                obj.telegram_id = request.user.telegram_id or ""
            obj.final_price = cart.get_cart_final_price()
            obj.save()

            if obj.telegram_id and not request.user.telegram_id:
                request.user.telegram_id = obj.telegram_id
                request.user.save()
            if not request.user.full_name:
                request.user.full_name = request.user.username
                request.user.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=obj,
                    product=item.product,
                )
            cart.delete()
            messages.success(request, gt_lazy("Your order is ready for payment."))
            return redirect('payment', obj.id)
    else:
        initial = {}
        if request.user.telegram_id:
            initial["telegram_id"] = request.user.telegram_id
        form = OrderCreationForm(initial=initial)

    return render(request, 'orders/order.html', context={
        'form': form,
        'username': request.user.username,
        'phone_number': request.user.phone or "",
        'telegram_id': request.user.telegram_id or "",
        'cart': cart,
    })
