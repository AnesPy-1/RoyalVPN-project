from django.forms import ModelForm

from .models import Payment

class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = [
            'payment_picture',
        ]
