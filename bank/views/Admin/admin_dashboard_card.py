from django.utils import timezone
from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from bank.models import User
from rest_framework import status

def get_time_range(period):
    now = timezone.now()

    if period == 'day':
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = current_start - timezone.timedelta(days=1)
    elif period == 'week':
        current_start = now - timezone.timedelta(days=now.weekday())
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
        current_start = timezone.datetime.min.replace(tzinfo=timezone.utc)
        previous_start = current_start
    else:
        raise ValueError("Invalid time period")

    return current_start, previous_start

@api_view(['GET'])
def user_growth(request, period):
    try:
        current_start, previous_start = get_time_range(period)
        now = timezone.now()

        current_period_users = User.objects.filter(created_at__range=(current_start, now)).count()
        previous_period_users = User.objects.filter(created_at__range=(previous_start, current_start)).count()

        if previous_period_users == 0:
            growth_percentage = 100.0 if current_period_users > 0 else 0.0
        else:
            growth_percentage = ((current_period_users - previous_period_users) / previous_period_users) * 100

        return Response({
            'status': True,
            'current_period_users': current_period_users,
            'previous_period_users': previous_period_users,
            'growth_percentage': growth_percentage
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
