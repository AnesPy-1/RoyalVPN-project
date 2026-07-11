from django import forms
from django.forms import ModelForm

from .models import Order

class OrderCreationForm(ModelForm):
    class Meta:
        model = Order
        fields = ('telegram_id',)
        labels = {
            'telegram_id': 'آیدی تلگرام',
        }
        help_texts = {
            'telegram_id': 'در صورت داشتن آیدی تلگرام، آن را وارد کنید.',
        }
        widgets = {
            'telegram_id': forms.TextInput(attrs={
                'class': 'checkout-input',
                'placeholder': '@username',
                'autocomplete': 'off',
            }),
        }
