from django.shortcuts import render, redirect
from subs.models import SubscriptionLinks, Subscriptions
from django.contrib import messages


def home_view(request):
    return render(request, 'shop/home.html')


def get_test(request):
    user = request.user

    if Subscriptions.objects.filter(user=user, is_test=True).exists():
        messages.info(request, "شما قبلا اشتراک تست خود را دریافت کرده‌اید!")
        return redirect('home')

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
                'test_sub':user_sub,
            }
        )
    messages.error(request, "هیچ اکانت تستی در دسترس نیست، لطفا با پشتیبانی در تماس باشید.")
    return redirect('home')

def pricing_view(request):
    return render(request, 'shop/pricing.html')