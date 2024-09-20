from django.utils import timezone 
from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from bank.models import User
from rest_framework import status
from ..functions import get_time_range
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
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
            "status":True,
            "data":{
                'status': True,
                'current': current_period_users,
                'previous': previous_period_users,
                'growth': growth_percentage
            }
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
