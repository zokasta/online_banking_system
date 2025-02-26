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
from .functions import generate_card_number
from datetime import datetime


@api_view(['POST'])
def signup(request):
    pan_regex = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    aadhar_regex = r'^\d{12}$'
    
    pan_card = request.data.get('pan_card', '').strip().upper()
    aadhar_card = request.data.get('aadhar_card', '').strip()
    dob = request.data.get('dob', '').strip()  # Date of birth in YYYY-MM-DD format

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
    
    try:
        dob_date = datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.now()
        age = (today - dob_date).days // 365
        if age < 18:
            return Response({
                'status': False,
                'message': 'You must be at least 18 years old to register.'
            })
    except ValueError:
        return Response({
            'status': False,
            'message': 'Invalid date format. Please use YYYY-MM-DD.'
        })

    serializer = UserSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()

        email = user.email
        email_username = email.split('@')[0]

        upi_id = f"{email_username}@zokasta"

        account_number = int(user.phone)
        debit_card = generate_card_number()
        expiration_date = generate_expiration_date()
        cvv = generate_cvv()

        account = Account.objects.create(
            user=user,
            account_number=account_number,
            debit_card=debit_card,
            expiration_date=expiration_date,
            cvv=cvv,
            balance=0,
            upi_id=upi_id 
        )
        account_serializer = AccountSerializer(account)

        otp = generate_otp()
        user.otp = otp
        user.save()

        # This is for sending OTP via email 
        # send_otp_email(user.email, otp)
        
        # Uncomment for sending OTP via SMS
        # messagehandler=MessageHandler(user.phone, otp).send_otp_via_message()
        
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
    user = User.objects.filter(username = request.data['username']).first()
    print(user)
    if not user:
        return Response({
            "status": False,
            "message": "Username or password is wrong"
        })
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
    if not user.is_superuser or not user.type == 'admin':
        return Response({
            "status": False,
            "message": "Access denied: not an admin"
        })

    if not user.check_password(request.data['password']):
        return Response({
            "status": False,
            "message": "Username or password is wrong"
        })

    otp = generate_otp()
    user.otp = otp
    user.save()

    # send_otp_email(user.email, otp)

    return Response({
        "status": True,
        "message": "OTP has been sent to your email",
        "otp":otp
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
def verify_otp(request):
    user = get_object_or_404(User, username=request.data['username'])
    otp = request.data.get('otp')

    if str(user.otp) == otp:
        Token.objects.filter(user=user).delete()

        token = Token.objects.create(user=user)

        user_serializer = UserSerializer(instance=user)

        account = get_object_or_404(Account, user=user)
        account_serializer = AccountSerializer(account)

        credit_card = CreditCard.objects.filter(user_id=user.id).first()
        user.otp = ""
        user.save()

        response_data = {
            'status': True,
            'token': token.key,
            'user': user_serializer.data,
            'account': account_serializer.data,
            'credit_card': False
        }

        if credit_card and credit_card.status == "confirm":
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

    otp = generate_otp()
    user.otp = otp
    user.save()

    # send_otp_email(user.email, otp)

    return Response({
        "status": True,
        "message": "OTP has been sent to your email"
    }, status=status.HTTP_200_OK)



@api_view(['POST'])
def verify_otp_for_forgot_password(request):
    username = request.data.get('username')
    otp = request.data.get('otp')
    user = get_object_or_404(User, username=username)

    if user.otp == otp:
        token = str(uuid.uuid4())
        user.reset_token = token
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

    if user.reset_token == token:
        user.set_password(new_password)
        user.reset_token = None
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




