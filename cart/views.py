from django.contrib import messages
from django.utils.text import gettext_lazy as gt
from django.shortcuts import render, get_object_or_404, redirect

from shop.models import Product
from .models import Cart, CartItem


def cart_detail_view(request):
    return render(request, 'cart/cart.html')


def add_to_cart_view(request, product_id):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

    product = get_object_or_404(Product, pk=product_id)

    CartItem.objects.create(cart=cart, product=product)
    messages.success(request, gt("Product successfully added to the cart."))
    return redirect('cart')


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    item.delete()
    messages.success(request, gt("Product has been removed from the cart."))
    return redirect('cart')




