from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('test/', views.get_test, name='get-test'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('about/', views.about_us_view, name='about'),
    path('faq/', views.faq_view, name='faq'),
    path('contact/', views.contact_view, name='contact'),
    path('get-sub/<int:order_id>/<int:payment_id>/', views.get_sub, name='get-sub')

]