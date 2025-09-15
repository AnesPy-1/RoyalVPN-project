from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'full_name',
            'email',
            'phone',
            'is_staff',
            'is_phone_verified',
            'date_joined',
            'telegram_id',
        ]

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'full_name',
            'email',
            'phone',
            'is_staff',
            'is_phone_verified',
            'date_joined',
            'telegram_id',
        ]