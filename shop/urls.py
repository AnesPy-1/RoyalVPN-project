from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('test/', views.get_test, name='get-test')
]