from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import RegexValidator


class State(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return f"Report by {self.name}"


class City(models.Model):
    name = models.CharField(max_length=50)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    def __str__(self):
        return f"Report by {self.name}"


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, email, username, password=None, **extra_fields):
        # extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('type', 'admin')
        

        # if extra_fields.get('is_staff') is not True:
        #     raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True)
    pan_card = models.CharField(max_length=10)
    aadhar_card = models.CharField(max_length=16)
    dob = models.DateField()
    mpin = models.CharField(max_length=6)
    type = models.CharField(max_length=20, choices=(('user', 'user'), ('admin', 'admin')))
    reset_token = models.TextField(null=True)
    
    gender = models.CharField(max_length=10, choices=(('male', 'Male'), ('female', 'Female'), ('other', 'Other')))

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_generated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_ban = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email


class Account(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_number = models.BigIntegerField(unique=True)
    debit_card = models.BigIntegerField()
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_frozen = models.BooleanField(default=False)
    cvv = models.CharField(
        max_length=3,
        validators=[RegexValidator(regex=r'^\d{3}$', message='CVV must be 3 digits')],
        default='123'
    )
    expiration_date = models.CharField(
        max_length=7,
        validators=[RegexValidator(regex=r'^(0[1-9]|1[0-2])\/\d{4}$', message='Expiration date must be in MM/YYYY format')],
        help_text="Enter the expiration date in MM/YYYY format"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Account {self.account_number} of user {self.user.email}'


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT_CARD = 'CC', 'Credit Card'
        DEBIT_CARD = 'DC', 'Debit Card'

    sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    type = models.CharField(
        max_length=2,
        choices=TransactionType.choices,
        default=TransactionType.CREDIT_CARD,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Transaction from {self.sender.user.email} to {self.receiver.user.email} for {self.amount}'

    def get_transaction_info(self):
        from django.utils import timezone
        formatted_date = self.created_at.strftime('%d %b %Y')
        status = 'Credit' if self.type == self.TransactionType.CREDIT_CARD else 'Debit'
        sender_name = self.sender.user.name
        receiver_name = self.receiver.user.name

        return {
            'index': self.pk,
            'amount': f'{self.amount}',
            'date': formatted_date,
            'status': status,
            'sender_name': sender_name,
            'receiver_name': receiver_name,
        }


class CreditCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card_number = models.CharField(
        max_length=16,
        validators=[RegexValidator(regex=r'^\d{16}$', message='Card number must be 16 digits')]
    )
    expiration_date = models.CharField(
        max_length=7,
        validators=[RegexValidator(regex=r'^(0[1-9]|1[0-2])\/\d{4}$', message='Expiration date must be in MM/YYYY format')]
    )
    cvv = models.CharField(
        max_length=4,
        validators=[RegexValidator(regex=r'^\d{3,4}$', message='CVV must be 3 or 4 digits')]
    )
    status = models.CharField(max_length=10,default="pending", choices=(('pending', 'pending'), ('confirm', 'confirm'), ('rejected', 'rejected')))
    is_freeze = models.BooleanField(default=False)
    
    limit_use = models.DecimalField(max_digits=10, decimal_places=2)
    used = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Credit Card {self.card_number} for User {self.user.email}'



class Report(models.Model):
    class Status(models.TextChoices):
        SEND = 'send', 'Send'
        SOLVED = 'solved', 'Solved'
        REJECTED = 'rejected', 'Rejected'

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(null=False)
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.SEND,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'Report by {self.user.username} with status {self.status}'

