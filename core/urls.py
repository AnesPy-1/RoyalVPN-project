from django.urls import path

from . import views

urlpatterns = [
    path('', views.sent_code_view, name='login'),
    path('verify/', views.verify_code_view, name='verify'),
]