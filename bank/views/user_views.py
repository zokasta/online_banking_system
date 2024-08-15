from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bank.models import User
from bank.serializers import UserSerializer
from rest_framework import status
from django.db.models import Q



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_authenticated_user(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response({
        'status': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_by_id(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return Response({
        'status': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    # Get the search query from request parameters
    search_query = request.query_params.get('search', '')

    # Build the query for case-insensitive search across multiple fields
    search_filter = Q()
    if search_query:
        search_filter |= Q(name__icontains=search_query)
        search_filter |= Q(username__icontains=search_query)
        search_filter |= Q(email__icontains=search_query)
        search_filter |= Q(phone__icontains=search_query)
        search_filter |= Q(pan_card__icontains=search_query)
        search_filter |= Q(aadhar_card__icontains=search_query)

    # Apply the search filter to the queryset
    users = User.objects.filter(search_filter)
    
    # Serialize users
    serializer = UserSerializer(users, many=True)
    
    # Add index and ID to each user's data
    user_data_with_index = []
    for index, user_data in enumerate(serializer.data, start=1):
        user_data['index'] = index
        user_data['id'] = user_data.get('id')  # Ensure the 'id' field is included
        user_data_with_index.append(user_data)
    
    return Response({
        'status': True,
        'users': user_data_with_index
    }, status=status.HTTP_200_OK)



@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user

    serializer = UserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)

    errors = {f"{field} field": next(iter(errors)) for field, errors in serializer.errors.items()}
    return Response({
        'status': False,
        'message': list(errors.values())[0]
    })



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_list(request):
    if request.user.type != 'admin':
        return Response({'error': 'You do not have permission to access this resource.'}, status=status.HTTP_403_FORBIDDEN)
    
    # Filter users to only include those with type='user'
    users = User.objects.filter(type='user')
    
    # Process each user to add status based on is_ban and index
    user_data = []
    for index, user in enumerate(users, start=1):
        serialized_user = UserSerializer(user).data
        # Add a custom status based on is_ban field
        serialized_user['status'] = 'frozen' if user.is_ban else 'normal'
        # Add index to the user data
        serialized_user['index'] = index
        user_data.append(serialized_user)
    
    return Response({'status': True, 'users': user_data})




@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    try:
        # Find the user by ID
        user = User.objects.get(id=user_id)
        user.delete()
        return Response({'status': True, 'message': 'User deleted successfully.'})
    except User.DoesNotExist:
        return Response({'status': False, 'message': 'User not found.'})



@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_update_by_admin(request, user_id):
    # if request.user.type != 'admin':
    #     return Response({'error': 'You do not have permission to access this resource.'})
    user = get_object_or_404(User, id=user_id)
    
    # Only allow updating of specific fields
    allowed_fields = {'name', 'phone', 'email'}
    data = {field: value for field, value in request.data.items() if field in allowed_fields}

    # Update the user's information
    serializer = UserSerializer(user, data=data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    errors = {f"{field} field": next(iter(errors)) for field, errors in serializer.errors.items()}
    return Response({
        'status': False,
        'message': list(errors.values())[0]
    })


