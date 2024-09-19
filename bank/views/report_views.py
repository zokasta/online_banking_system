from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from ..models import Report
from ..serializers import ReportSerializer

# View for creating a new report
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only authenticated users can submit reports
def create_report(request):
    # Set the user in the request data
    data = request.data.copy()
    data['user'] = request.user.id
    
    # Serialize and validate the report data
    serializer = ReportSerializer(data=data)
    if serializer.is_valid():
        serializer.save()  # Save the report
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View for retrieving the user's reports
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Only authenticated users can view their own reports
def get_reports(request):
    reports = Report.objects.filter(user=request.user)  # Filter reports by the logged-in user
    serializer = ReportSerializer(reports, many=True)  # Serialize the list of reports
    return Response(serializer.data, status=status.HTTP_200_OK)
