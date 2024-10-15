from datetime import timezone as dt_timezone
from django.utils import timezone
from django.db.models import Sum
from ..models import Transaction, CreditCard, Account
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta


def digits_of(n):
    return [int(d) for d in str(n)]  # Ensure n is a string or integer


def get_time_range(period):
    now = timezone.now()

    if period == 'day':
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start - timezone.timedelta(days=1)
    elif period == 'week':
        # Calculate the start of the current week
        current_start = now - timezone.timedelta(days=now.weekday())
        current_start = current_start.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start - timezone.timedelta(weeks=1)
    elif period == 'month':
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month = current_start - timezone.timedelta(days=1)
        previous_start = previous_month.replace(day=1)
    elif period == 'year':
        current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_year = current_start - timezone.timedelta(days=1)
        previous_start = previous_year.replace(month=1, day=1)
    elif period == 'all':
        current_start = timezone.datetime.min.replace(tzinfo=dt_timezone.utc)
        previous_start = current_start
    else:
        raise ValueError("Invalid time period")

    return current_start, previous_start


def get_last_six_months():
    now = timezone.now()
    six_months_ago = now - timezone.timedelta(days=180)
    months = []
    month_names = []

    for i in range(6):
        month_start = six_months_ago.replace(day=1)
        month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(seconds=1)
        month_names.append(month_start.strftime('%b %Y'))
        months.append((month_start, month_end))
        six_months_ago += timezone.timedelta(days=32)

    return month_names, months


def get_six_month_transaction():
    month_names, months = get_last_six_months()
    transaction_sums = []

    for start, end in months:
        # Ensure both start and end are timezone-aware if necessary
        total = Transaction.objects.filter(created_at__range=(start, end)).aggregate(Sum('amount'))['amount__sum'] or 0
        transaction_sums.append(total)

    return month_names, transaction_sums


def generate_expiration_date(years_from_now=3):
    now = datetime.now()
    expiration_date = now + relativedelta(years=years_from_now)
    return expiration_date.strftime('%m/%y')


def generate_cvv():
    return str(random.randint(100, 999)).zfill(3)


def get_six_month_credit_card_transactions(user):
    id = user.id
    month_names, months = get_last_six_months()
    transaction_sums = []

    if user.type == 'admin':
        for start, end in months:
            transactions = Transaction.objects.filter(created_at__range=(start, end),type='CC').aggregate(Sum('amount'))['amount__sum'] or 0
            transaction_sums.append(transactions)
    else:
         for start, end in months:
            transactions = Transaction.objects.filter(created_at__range=(start, end),type='CC',sender_id=id).aggregate(Sum('amount'))['amount__sum'] or 0
            transaction_sums.append(transactions)


    return month_names, transaction_sums


def get_six_month_debit_card_transactions(user):
    id = user.id
    month_names, months = get_last_six_months()
    transaction_sums = []

    if user.id == 'admin':
        for start, end in months:
            transactions = Transaction.objects.filter(created_at__range=(start, end),type='DC').aggregate(Sum('amount'))['amount__sum'] or 0
            transaction_sums.append(transactions)
    else:
        for start, end in months:
            transactions = Transaction.objects.filter(created_at__range=(start, end),type='DC',sender_id=id).aggregate(Sum('amount'))['amount__sum'] or 0
            transaction_sums.append(transactions)
    return month_names, transaction_sums

 # Import your models


def generate_card_number(prefix="4", length=16):
    """
    Generate a unique valid credit card number using the Luhn algorithm.
    The number will have the specified prefix and be of the given length.
    The generated card number will also be checked against both the Account
    (debit_card) and CreditCard (card_number) tables to ensure uniqueness.
    """
    
    def card_number_exists(card_number):
        """
        Check if the card number exists in the Account's debit_card or CreditCard's card_number.
        """
        debit_card_exists = Account.objects.filter(debit_card=card_number).exists()
        credit_card_exists = CreditCard.objects.filter(card_number=card_number).exists()
        return debit_card_exists or credit_card_exists

    def luhn_checksum(card_number):
        """
        Calculate the Luhn checksum for the given card number as a string.
        """
        def digits_of(n):
            return [int(digit) for digit in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10

    card_number = None
    
    while not card_number or card_number_exists(card_number):
        # Generate a potential card number
        card_number = [int(x) for x in prefix]

        # Generate random digits to fill the rest of the card number (except the last one)
        while len(card_number) < (length - 1):
            card_number.append(random.randint(0, 9))

        # Calculate the checksum digit using the Luhn algorithm
        card_number_as_string = ''.join(map(str, card_number))
        checksum_digit = luhn_checksum(card_number_as_string + '0')
        if checksum_digit != 0:
            checksum_digit = 10 - checksum_digit
        
        # Append the checksum to the card number
        card_number.append(checksum_digit)
        
        # Join the card number list into a single string
        card_number = ''.join(map(str, card_number))
    
    # Return a unique card number
    return card_number





