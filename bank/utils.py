import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return random.randint(100000, 999999)

def send_otp_email(email, otp):
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
