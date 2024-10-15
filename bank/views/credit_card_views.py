from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from ..models import CreditCard, Account
from .functions import generate_card_number, generate_expiration_date, generate_cvv
from ..permissions import IsAdminUserType, IsUserType


# @csrf_exempt  
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def apply_for_credit_card(request):
    user = request.user  # Get the authenticated user

    # Check if the user already has a credit card
    if CreditCard.objects.filter(user=user).exists():
        return Response({'status': False, 'message': 'You already send the application.'})

    # Generate credit card details
    card_number = generate_card_number()  # Implemented generate_card_number
    expiration_date = generate_expiration_date()  # Generates expiration date, e.g., 3 years from now
    cvv = generate_cvv()  # Generates a random CVV

    try:
        # Create the new credit card
        new_credit_card = CreditCard.objects.create(
            user=user,
            card_number=card_number,
            expiration_date=expiration_date,
            cvv=cvv,
            limit_use=30000,  # Example credit limit
            status='pending',
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        return Response({'status': True, 'message': 'Credit card application successful.'}, status=201)

    except Exception as e:
        return Response({'status': False, 'message': f'Failed to create credit card: {str(e)}'})



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def get_credit_card_list(request):
    user = request.user  # Get the authenticated user

    # Get the search parameter from the query string, default is empty string
    search = request.query_params.get('search', '').strip()

    # Get all credit cards for the user
    credit_cards = CreditCard.objects.filter(user=user)

    # Filter credit cards based on the search query
    if search:
        credit_cards = credit_cards.filter(
            card_number__icontains=search  # You can adjust this to search by other fields if needed
        )

    # Prepare the list of credit cards with an index and formatted details
    credit_card_list = []
    for idx, credit_card in enumerate(credit_cards, start=1):
        credit_card_list.append({
            "index": idx,
            "card_number": credit_card.card_number,
            "expiration_date": credit_card.expiration_date,
            "cvv": credit_card.cvv,
            "status": credit_card.status,
            "is_freeze": credit_card.is_freeze,
            "limit_use": credit_card.limit_use,
            "created_at": credit_card.created_at.strftime('%d %b %Y, %H:%M:%S'),
            "updated_at": credit_card.updated_at.strftime('%d %b %Y, %H:%M:%S'),
        })

    return Response({
        "status": True,
        "data":{
            "credit_cards": credit_card_list
        }
    }, status=200)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def get_credit_card_usage(request):
    user_id = request.user.id
    try:
        credit_card = CreditCard.objects.get(user_id=user_id)
        left_limit = credit_card.limit_use- credit_card.used
        return Response({
            "status": True,
            "data": left_limit
        }, status=200)
    except CreditCard.DoesNotExist:
        return Response({
            "status": False,
            "message": "No credit card found for this user."
        })
    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        })



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def pay_credit_card_bills(request):
    user_id = request.user.id 

    try:
        mpin = request.data.get('mpin')
        account = Account.objects.get(user_id=user_id)
        credit_card = CreditCard.objects.get(user_id=user_id)
        user_mpin = request.user.mpin
        
        if mpin != user_mpin:
            return Response({
                "status": False,
                "message": "MPIN is not a valid"
            })
            

        # Get the outstanding amount (used) from the credit card
        payment_amount = credit_card.used

        # Check if the user has enough balance in their account
        if account.balance < payment_amount:
            return Response({
                "status": False,
                "message": "Insufficient balance in your account."
            })

        # Check if the credit card has any outstanding balance
        if credit_card.used == 0:
            return Response({
                "status": False,
                "message": "No outstanding balance on your credit card."
            })

        # Deduct the payment from the user's account
        account.balance -= payment_amount
        account.save()

        # Transfer the payment to the account with ID 1
        try:
            receiving_account = Account.objects.get(id=1)
            receiving_account.balance += payment_amount
            receiving_account.save()
        except Account.DoesNotExist:
            return Response({
                "status": False,
                "message": "Receiving account with ID 1 does not exist."
            })

        # Deduct the payment from the credit card's used amount
        credit_card.used = 0  # Since the full amount is being paid, set used to 0
        credit_card.updated_at = timezone.now()  # Update the timestamp
        credit_card.save()

        return Response({
            "status": True,
            "message": "Payment successful.",
            "user_account_balance": account.balance,
            "paid_amount": payment_amount
        }, status=200)

    except Account.DoesNotExist:
        return Response({
            "status": False,
            "message": "User account not found."
        })

    except CreditCard.DoesNotExist:
        return Response({
            "status": False,
            "message": "No credit card found for this user."
        })

    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        })






