from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.sent_code_view, name='login'),
    path('verify/', views.verify_code_view, name='verify'),
    path('dashboard/', views.user_dashboard_view, name='dashboard')
]