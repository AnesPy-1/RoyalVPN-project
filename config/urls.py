from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.forms import PersianAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('cart/', include('cart.urls')),
    path('checkout/', include('orders.urls')),
    path('payment/', include('payment.urls')),
    path('api/bot/', include('botapi.urls')),
    path('', include('core.urls')),
    path('login/', auth_views.LoginView.as_view(authentication_form=PersianAuthenticationForm), name='login'),
    path('', include('django.contrib.auth.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
