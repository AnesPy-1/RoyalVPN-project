from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from core.forms import CustomUserCreationForm
from core.models import CustomUser


@login_required
def user_dashboard_view(request):
    user_orders = request.user.user_orders.all()
    return render(request, 'core/dashboard.html', context={'orders':user_orders, 'wallet_balance': request.user.wallet_balance})


class SignUpView(generic.CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def get_success_url(self):
        return reverse('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        raw_password = form.cleaned_data.get("password1")
        if raw_password:
            authenticated = authenticate(
                self.request,
                username=self.object.username,
                password=raw_password,
            )
            if authenticated is not None:
                login(self.request, authenticated)
        return response
