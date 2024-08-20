from datetime import timezone as dt_timezone
from django.utils import timezone
from django.db.models import Sum
from ..models import Transaction
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta


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
    return str(random.randint(100, 9999)).zfill(3)
