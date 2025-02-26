from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bank.models import User
from bank.serializers import UserSerializer
from rest_framework import status
from django.db.models import Q
from ..permissions import IsAdminUserType, IsUserType


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
@permission_classes([IsAuthenticated, IsAdminUserType])
def get_all_users(request):
    search_query = request.query_params.get('search', '')

    search_filter = Q()
    if search_query:
        search_filter |= Q(name__icontains=search_query)
        search_filter |= Q(username__icontains=search_query)
        search_filter |= Q(email__icontains=search_query)
        search_filter |= Q(phone__icontains=search_query)
        search_filter |= Q(pan_card__icontains=search_query)
        search_filter |= Q(aadhar_card__icontains=search_query)

    users = User.objects.filter(search_filter)
    
    serializer = UserSerializer(users, many=True)
    
    user_data_with_index = []
    for index, user_data in enumerate(serializer.data, start=1):
        user_data['index'] = index
        user_data['id'] = user_data.get('id')
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
    
    users = User.objects.filter(type='user')
    
    user_data = []
    for index, user in enumerate(users, start=1):
        serialized_user = UserSerializer(user).data
        serialized_user['status'] = 'frozen' if user.is_ban else 'normal'
        serialized_user['index'] = index
        user_data.append(serialized_user)
    
    return Response({'status': True, 'users': user_data})




@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return Response({'status': True, 'message': 'User deleted successfully.'})
    except User.DoesNotExist:
        return Response({'status': False, 'message': 'User not found.'})



@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_update_by_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    allowed_fields = {'name', 'phone', 'email'}
    data = {field: value for field, value in request.data.items() if field in allowed_fields}

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



@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_user_ban(request, user_id):
    user = get_object_or_404(User, id=user_id)

    is_ban = request.data.get('status', 'none')
    if is_ban == 'none':
        is_ban = False
    elif is_ban == 'ban':
        is_ban = True

    if is_ban is not None:
        user.is_ban = is_ban
        user.save()

        status_text = 'banned' if is_ban else 'unbanned'
        return Response({
            'status': True,
            'message': f'User has been {status_text}.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': False,
            'message': 'Please provide a valid is_ban value (True or False).'
        }, status=status.HTTP_400_BAD_REQUEST)



