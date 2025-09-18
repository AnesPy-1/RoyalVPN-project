from melipayamak import Api
from django.conf import settings


from .models import OTP



def send_otp(phone, code):
    api = Api(settings.MELIPAYAMAK_USERNAME, settings.MELIPAYAMAK_PASSWORD)
    sms = api.sms()

    # sms.send(phone, settings.MELIPAYAMAK_NUMBER)

    sms.send_by_base_number(f"کد ورود شما:\n\t{code}", phone, settings.MELIPAYAMAK_BODYID)

