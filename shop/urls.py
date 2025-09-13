from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('test/', views.get_test, name='get-test'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('about/', views.about_us_view, name='about'),
    path('faq/', views.faq_view, name='faq-view'),
    path('contact/', views.contact_view, name='contact')
]