from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.contrib import messages
from django.utils.text import gettext_lazy as _

from core.forms import CustomUserCreationForm
from core.models import CustomUser


@login_required
def user_dashboard_view(request):
    user_orders = request.user.user_orders.all()
    return render(request, 'core/dashboard.html', context={'orders':user_orders})


class SignUpView(generic.CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def get_success_url(self):
        return reverse('login')

    def form_valid(self, form):
        return super().form_valid(form)