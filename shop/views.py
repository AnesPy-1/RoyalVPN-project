from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from orders.models import Order
from payment.models import Payment
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
        user_exist_sub_link = Subscriptions.objects.filter(user=user, is_test=True).first()
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


def get_sub(request, order_id, payment_id):
    order = get_object_or_404(Order, pk=order_id)
    payment = get_object_or_404(Payment, pk=payment_id)

    created_subs = []

    if order.status != Order.OrderStatus.PAID:
        messages.error(request, "سفارش پرداخت نشده است.")
        return redirect('home')
    if order.user != request.user or payment.user != request.user:
        messages.error(request, "خطا در اطلاعات ورودی")
        return redirect('home')

    if payment.is_used:
        for item in payment.subs.all():
            created_subs.append(item)

        messages.error(request, "سفارش قبلا تحویل شده است.")
        return render(request, "shop/get_sub.html", context={'user_exists_subscriptions': created_subs})


    for item in order.items.all():
        sub = SubscriptionLinks.objects.filter(
            plan_type=SubscriptionLinks.TypeChoices.SUB,
            day_limit=item.product.time_limit_NUM,
            traffic_limit=item.product.traffic_limit,
            is_test=False,
            is_used=False,
        ).first()
        if sub:
            user_sub = Subscriptions.objects.create(
                user=request.user,
                sub=sub,
            )
            created_subs.append(sub)
            sub.is_used = True
            sub.save()
            payment.subs.add(user_sub)
            payment.save()
            item.is_completed = True
            item.save()

        else:
            order.status = Order.OrderStatus.FAILED
            messages.info(
                request,
                f"مشکل در ساخت اکانت برای سفارش شماره {order.id}، لطفا با پشتیبانی در تماس باشید."
            )

    if created_subs:
        payment.is_used = True
        payment.save()
        messages.success(request, "اکانت شما آماده استفاده است.")
        return render(request, "shop/get_sub.html", context={'user_subscriptions': created_subs})
    else:
        return redirect('home')