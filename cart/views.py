from django.shortcuts import render
from django.db.models import Prefetch

from .models import Cart, CartItem


def cart_detail_view(request):
    return render(request, 'cart/cart.html')