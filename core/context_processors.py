from django.db.models import Prefetch

from .models import SiteSettings, FrequentlyAskedQuestions
from cart.models import Cart, CartItem


def site_context(request):
    site_settings = SiteSettings.objects.all().first()
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    context = {'site_context':site_settings, 'cart':cart}
    if request.user.is_authenticated:
        context["wallet_balance"] = getattr(request.user, "wallet_balance", 0)
    return context
