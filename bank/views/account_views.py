from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import Account
from django.db import transaction
from ..permissions import IsAdminUserType, IsUserType



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def admin_account_list(request):
    search = request.query_params.get('search', '').strip()

    accounts = Account.objects.all()

    if search:
        accounts = accounts.filter(
            balance__icontains=search) | accounts.filter(
            user__name__icontains=search) | accounts.filter(
            debit_card__icontains=search) | accounts.filter(
            created_at__icontains=search)

    accounts = accounts.order_by('-created_at')

    account_list = []
    for idx, account in enumerate(accounts, start=1):
        account_list.append({
            "index": idx,
            "id": account.id,
            "balance": f'{account.balance}',
            "name": account.user.name,
            "debit_card": account.debit_card,
            "created_at": account.created_at.strftime('%d %b %Y, %H:%M:%S'),
            "is_frozen": account.is_frozen,
        })

    return Response({
        "status": True,
        "accounts": account_list
    }, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def admin_account_delete(request, account_id):
    account = get_object_or_404(Account, id=account_id)

    account.delete()

    return Response({
        "status": True,
        "message": f"Account with ID {account_id} has been deleted."
    }, status=status.HTTP_200_OK)




@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def admin_account_edit(request, account_id):
    account = get_object_or_404(Account, id=account_id)

    # Get data from the request
    name = request.data.get('name')
    balance = request.data.get('balance')
    debit_card = request.data.get('debit_card')

    # Validate data
    if not name or not balance or not debit_card:
        return Response({
            "status": False,
            "message": "All fields (name, balance, debit_card) are required."
        })

    try:
        with transaction.atomic():
            # Update account fields
            account.user.name = name
            account.balance = balance
            account.debit_card = debit_card
            account.user.save()  # Save the related user model if needed
            account.save()

            return Response({
                "status": True,
                "message": f"Account with ID {account_id} has been updated."
            })

    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        })





@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_account_freeze(request, account_id):
    account = get_object_or_404(Account, id=account_id)

    is_frozen = request.data.get('status', None)
    if is_frozen == 'none':
        is_frozen = False
    elif is_frozen == 'freeze':
        is_frozen = True
    else:
        return Response({
            'status': False,
            'message': 'Please provide a valid status value (none or freeze).'
        }, status=status.HTTP_400_BAD_REQUEST)  

    if is_frozen is not None:
        account.is_frozen = is_frozen
        account.save()

        status_text = 'frozen' if is_frozen else 'unfrozen'
        return Response({
            'status': True,
            'message': f'Account has been {status_text}.'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'status': False,
            'message': 'Please provide a valid is_frozen value (True or False).'
        }, status=status.HTTP_400_BAD_REQUEST)




