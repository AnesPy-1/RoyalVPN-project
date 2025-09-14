from django.shortcuts import render
from django.db.models import Prefetch

from .models import Cart, CartItem


def cart_detail_view(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

    cart = Cart.objects.filter(pk=cart.pk).prefetch_related(
            Prefetch(
                'items',
                queryset=CartItem.objects.select_related('product')
            )
        ).select_related('user')

    context = {
        'cart':cart,
    }
    return render(request, 'cart/cart.html', context=context)