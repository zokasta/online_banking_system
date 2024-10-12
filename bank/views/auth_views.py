import uuid
import re
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from bank.serializers import UserSerializer, AccountSerializer, CreditCardSerializer
from bank.models import User, Account, CreditCard
from bank.utils import generate_otp, send_otp_email
from rest_framework import status
from ..Massage import MessageHandler
from .functions import generate_expiration_date, generate_cvv
import random


def generate_card_number():
    while True:
        card_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        if not Account.objects.filter(debit_card=card_number).exists():
            return card_number


@api_view(['POST'])
def signup(request):
    # return Response({request})
    pan_regex = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    aadhar_regex = r'^\d{12}$'
    
    pan_card = request.data.get('pan_card', '').strip().upper()
    aadhar_card = request.data.get('aadhar_card', '').strip()
    if not re.match(pan_regex, pan_card):
        return Response({
            'status': False,
            'message': 'Invalid PAN card number. Please enter a valid PAN.'
        })
    
    if not re.match(aadhar_regex, aadhar_card):
        return Response({
            'status': False,
            'message': 'Invalid Aadhar card number. Please enter a valid 12-digit Aadhar number.'
        })

    serializer = UserSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()

        # Additional account creation logic
        account_number = int(user.phone)
        debit_card = generate_card_number()
        expiration_date =generate_expiration_date()
        cvv = generate_cvv()

        account = Account.objects.create(
            user=user,
            account_number=account_number,
            debit_card=debit_card,
            expiration_date=expiration_date,
            cvv=cvv,
            balance=0
        )
        account_serializer = AccountSerializer(account)

        otp = generate_otp()
        user.otp = otp
        user.save()

        # send_otp_email(user.email, otp)

        return Response({
            'status': True,
            'otp': otp,
            'message': 'OTP has been sent to your email',
            'user': serializer.data,
            'account': account_serializer.data
        })

    errors = {f"{field} field is required": next(iter(errors)) for field, errors in serializer.errors.items()}
    return Response({
        'status': False,
        'message': list(errors.values())[0]
    }, status=status.HTTP_200_OK)
    


@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return Response({
            "status": False,
            "message": "Username or password is wrong"
        })

    if not user.type == 'user':
        return Response({
            'status': False,
            'message': "You don't have permission to login"
        }) 
    otp = generate_otp()
    user.otp = otp
    user.save()

    # messagehandler=MessageHandler(user.phone,otp).send_otp_via_message()
    # send_otp_email(user.email, otp)

    return Response({
        "status": True,
        "otp":otp,
        "message": "OTP has been sent to your email"
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
def adminLogin(request):
    user = get_object_or_404(User, username=request.data['username'])
    # account = get_object_or_404(Account, user_id=user.id)
    # Check if the user is an admin
    if not user.is_superuser or not user.type == 'admin':
        return Response({
            "status": False,
            "message": "Access denied: not an admin"
        })

    # Check the password
    if not user.check_password(request.data['password']):
        return Response({
            "status": False,
            "message": "Username or password is wrong"
        })

    # Generate and save OTP
    otp = generate_otp()
    user.otp = otp
    user.save()

    # Send OTP via email
    send_otp_email(user.email, otp)

    return Response({
        "status": True,
        "message": "OTP has been sent to your email",
        "otp":otp
        # "account":account
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def verify_otp(request):
    user = get_object_or_404(User, username=request.data['username'])
    otp = request.data.get('otp')

    if str(user.otp) == otp:
        # Delete any existing tokens for this user
        Token.objects.filter(user=user).delete()

        # Create a new token for the user
        token = Token.objects.create(user=user)

        # Serialize the user data
        user_serializer = UserSerializer(instance=user)

        # Query and serialize the associated account
        account = get_object_or_404(Account, user=user)
        account_serializer = AccountSerializer(account)

        # Fetch credit card details if any
        credit_card = CreditCard.objects.filter(user_id=user.id).first()
        user.otp = ""
        user.save()

        response_data = {
            'status': True,
            'token': token.key,
            'user': user_serializer.data,
            'account': account_serializer.data,
            'credit_card': False  # Default to False if no credit card is found
        }

        # Check if credit_card exists and if its status is "active"
        if credit_card and credit_card.status == "confirm":
            # Serialize the credit card details
            credit_card_serializer = CreditCardSerializer(credit_card)
            response_data["credit_card"] = True
            response_data["credit_card_data"] = credit_card_serializer.data

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": False,
            "message": "OTP is incorrect"
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
def send_otp_for_forgot_password(request):
    email = request.data.get('email')
    user = get_object_or_404(User, email=email)

    # Generate and save OTP
    otp = generate_otp()
    user.otp = otp
    user.save()

    # Send OTP to user's email
    send_otp_email(user.email, otp)

    return Response({
        "status": True,
        "message": "OTP has been sent to your email"
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
def verify_otp_for_forgot_password(request):
    username = request.data.get('username')
    otp = request.data.get('otp')
    user = get_object_or_404(User, username=username)

    # Verify OTP
    if user.otp == otp:
        # Generate unique token
        token = str(uuid.uuid4())
        user.reset_token = token  # Assuming you have a reset_token field in User model
        user.save()

        return Response({
            "status": True,
            "token": token
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": False,
            "message": "Invalid OTP"
        }, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def reset_password(request):
    username = request.data.get('username')
    token = request.data.get('token')
    new_password = request.data.get('password')
    user = get_object_or_404(User, username=username)

    # Verify token
    if user.reset_token == token:
        user.set_password(new_password)
        user.reset_token = None  # Clear the token after use
        user.save()

        return Response({
            "status": True,
            "message": "Password has been reset successfully"
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": False,
            "message": "Invalid token"
        }, status=status.HTTP_400_BAD_REQUEST)




