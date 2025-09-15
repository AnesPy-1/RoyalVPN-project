from django.urls import path

from . import views

urlpatterns = [
    path('pay/<int:order_id>', views.payment_creation_view, name='payment'),
]