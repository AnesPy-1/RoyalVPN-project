from django.urls import path

from . import views

urlpatterns = [
    path('', views.cart_detail_view, name='cart'),
    path('add/<str:product_id>', views.add_to_cart_view, name='cart-add'),
    path('remove/<str:item_id>/', views.remove_from_cart, name='cart-remove'),
]
