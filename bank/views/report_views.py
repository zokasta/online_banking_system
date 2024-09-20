from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Report
from ..serializers import ReportSerializer


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_report(request):
    # Set the user in the request data
    data = request.data.copy()
    data['user'] = request.user.id
    data['message'] = request.data.get('message')
    # data['custom_name'] = request.user.name
    
    # Serialize and validate the report data
    serializer = ReportSerializer(data=data)
    if serializer.is_valid():
        serializer.save()  # Save the report
        return Response({
            'status': True,
            'message': 'Report created successfully.',
            'data': serializer.data
        })
    else:
        # If validation fails, return errors with status and message
        return Response({
            'status': False,
            'message': 'Failed to create report. Please check the provided data.',
            'errors': serializer.errors
        })


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_reports(request):
    reports = Report.objects.filter(user=request.user)  # Filter reports by the logged-in user
    serializer = ReportSerializer(reports, many=True)  # Serialize the list of reports
    return Response({
        'status': True,
        'message': 'Reports retrieved successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)
