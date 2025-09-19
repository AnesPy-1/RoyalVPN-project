from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from django.utils.text import gettext_lazy as gt_lazy

from cart.models import Cart, CartItem
from .forms import OrderCreationForm
from .models import OrderItem


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
            obj.final_price = cart.get_cart_final_price()
            obj.save()

            if not request.user.telegram_id:
                request.user.telegram_id = obj.telegram_id
                request.user.save()
            if not request.user.full_name:
                request.user.full_name = obj.name
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
        form = OrderCreationForm()

    return render(request, 'orders/order.html', context={
        'form':form,
    })
