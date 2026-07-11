from django.urls import path

from . import views

urlpatterns = [
    path('', views.order_create_view, name='checkout'),
    path('delete/<int:order_id>/', views.order_delete_view, name='order-delete'),
]
