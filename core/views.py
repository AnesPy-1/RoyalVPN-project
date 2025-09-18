from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.text import gettext_lazy as _
from django.shortcuts import render, redirect

from .models import CustomUser, OTP
from .utils import send_otp

def sent_code_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')

        code = OTP.generate_code()

        OTP.objects.update_or_create(
            phone=phone,
            defaults={'code':code}
        )

        send_otp(phone, code)

        request.session['phone'] = phone
        messages.success(request, _("Please enter the 6-digit code that was sent to you via SMS."))
        return redirect("verify")
    return render(request, "core/send_code.html")


def verify_code_view(request):
    phone = request.session.get('phone')
    if not phone:

        return redirect('login')

    if request.method == 'POST':
        code = request.POST.get('code')

        otp = OTP.objects.filter(phone=phone, code=code, is_used=False).first()

        if otp and otp.is_valid():

            otp.is_used = True
            otp.save()
            user, created = CustomUser.objects.get_or_create(phone=phone)

            login(request, user)
            messages.success(request, _("Welcome"))
            return redirect('home')
        messages.error(request, _("The code you entered is incorrect. Please try again."))
        return render(request, 'core/verify_code.html')

@login_required
def user_dashboard_view(request):
    user_orders = request.user.user_orders.all()
    return render(request, 'core/dashboard.html', context={'orders':user_orders})

