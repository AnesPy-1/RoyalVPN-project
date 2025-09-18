from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

def redirect_to_fa(request):
    return redirect('/fa/')

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('cart/', include('cart.urls')),
    path('checkout/', include('orders.urls')),
    path('payment/', include('payment.urls')),
    path('register/', include('core.urls'))
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
