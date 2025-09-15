from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from subs.models import SubscriptionLinks, Subscriptions
from django.contrib import messages

from core.models import FrequentlyAskedQuestions
from .models import Product, Comment

def home_view(request):
    comments = Comment.objects.all()[:9]
    return render(request, 'shop/home.html', context={'comments':comments})

#@login_required
def get_test(request):
    user = request.user
    user_exist_subscription = Subscriptions.objects.filter(user=user, is_test=True)

    if user_exist_subscription.exists():
        user_exist_sub_link = Subscriptions.objects.filter(user=user, is_test=True).first().sub.sub_link
        messages.info(request, "شما قبلا اشتراک تست خود را دریافت کرده‌اید!")
        return render(
            request,
            'shop/get_sub.html',
            context={
                'user_exist_sub_link': user_exist_sub_link,
            }
        )

    test_link = SubscriptionLinks.objects.filter(is_test=True, is_used=False).first()

    if test_link:
        test_link.is_used = True
        test_link.save()
        user_sub = Subscriptions.objects.create(
            user=user,
            sub=test_link,
            is_test=True,
        )
        messages.success(request, "اکانت تست شما آماده استفاده است!")
        return render(
            request,
            'shop/get_sub.html',
            context={
                'test_link':test_link,
            }
        )
    messages.error(request, "هیچ اکانت تستی در دسترس نیست، لطفا با پشتیبانی در تماس باشید.")
    return redirect('home')

def pricing_view(request):
    products = Product.objects.all()
    return render(request, 'shop/pricing.html', context={'products':products})

def about_us_view(request):
    return render(request, 'shop/about.html')

# Frequently Asked Questions

def faq_view(request):
    faqs = FrequentlyAskedQuestions.objects.prefetch_related('answers')
    return render(request, 'shop/faq.html', context={'faqs':faqs})

def contact_view(request):
    return render(request, 'shop/contact.html')