from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction as db_transaction
from ..models import Account, Transaction, User
from ..serializers import TransactionSerializer, AccountSerializer
from rest_framework import status
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .functions import get_time_range,get_six_month_transaction



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    sender = request.user
    sender_account = get_object_or_404(Account, user=sender)
    amount = request.data.get('amount', 0)
    email = request.data.get('email')
    mpin = request.data.get('mpin')

    # Fetch the receiver's user object using the email
    receiver_user = get_object_or_404(User, email=email)
    
    if sender.mpin != mpin:
        return Response({
            "status": False,
            "message": "Invalid MPIN",
        }, status=status.HTTP_200_OK)

    # Get the receiver's account
    receiver_account = get_object_or_404(Account, user=receiver_user)
    # return Response(sender_account.balance)
    if sender_account.balance < amount:
        return Response({
            "status": False,
            "message": "Insufficient funds"
        }, status=status.HTTP_200_OK)

    # Perform the transaction
    sender_account.balance -= amount
    sender_account.save()

    receiver_account.balance += amount
    receiver_account.save()

    # Create the transaction record
    transaction_data = {
        'sender': sender_account.id,
        'receiver': receiver_account.id,
        'amount': amount
    }

    serializer = TransactionSerializer(data=transaction_data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': True,
            'transaction': serializer.data
        }, status=status.HTTP_201_CREATED)

    errors = {f"{field} field": next(iter(errors)) for field, errors in serializer.errors.items()}
    return Response({
        'status': False,
        'message': list(errors.values())[0]
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def see_balance(request):
    account = get_object_or_404(Account, user=request.user)
    serializer = AccountSerializer(account)
    return Response({
        "status": True,
        "balance": serializer.data['balance']
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    account = get_object_or_404(Account, user=request.user)
    search = request.query_params.get('search', '').strip()

    # Get both sent and received transactions
    sent_transactions = Transaction.objects.filter(sender=account)
    received_transactions = Transaction.objects.filter(receiver=account)

    # Use a dictionary to avoid duplicates
    transactions_dict = {}

    # Add sent transactions
    for transaction in sent_transactions:
        transactions_dict[transaction.pk] = {
            "transaction": transaction,
            # Set status as 'Debit' if user is the sender
            "status_info": 'Debit'
        }

    # Add received transactions, checking for duplicates
    for transaction in received_transactions:
        if transaction.pk not in transactions_dict:
            transactions_dict[transaction.pk] = {
                "transaction": transaction,
                # Set status as 'Credit' if user is the receiver
                "status_info": 'Credit'
            }
        else:
            # If already present, we can assume the status was set correctly in the sent transactions loop
            transactions_dict[transaction.pk]["status_info"] = 'Self Transfer'

    # Convert the dictionary to a list of transactions
    transactions = list(transactions_dict.values())

    # Sort by timestamp
    transactions.sort(key=lambda t: t["transaction"].created_at, reverse=True)

    # Filter transactions based on the search term
    filtered_transactions = []
    for idx, trans_dict in enumerate(transactions, start=1):
        transaction = trans_dict["transaction"]
        status_info = trans_dict["status_info"]

        # Determine the name of the other party
        if transaction.sender == account:
            name = transaction.receiver.user.name
        else:
            name = transaction.sender.user.name

        # Format timestamp
        formatted_timestamp = transaction.created_at.strftime('%d %b %Y, %H:%M:%S')

        # Check if search term matches name, timestamp, amount, or status
        if (
            search.lower() in name.lower() or
            search in formatted_timestamp or
            search in status_info.lower() or
            search in str(transaction.amount)
        ):
            filtered_transactions.append({
                "index": idx,
                "name": name,
                "status": status_info,
                "amount": transaction.amount,
                "timestamp": formatted_timestamp,
            })

    return Response({
        "status": True,
        "transactions": filtered_transactions
    }, status=status.HTTP_200_OK)




@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def show_transaction(request):
    user = request.user
    # Get the user's account
    account = get_object_or_404(Account, user=user)

    # Get the search keyword from the request data
    search_keyword = request.data.get('search', '')

    # Query for transactions where the user is either sender or receiver
    transactions = Transaction.objects.filter(sender=account) | Transaction.objects.filter(receiver=account)

    
    # Apply search filter
    if search_keyword:
        transactions = transactions.filter(
            sender__user__name__icontains=search_keyword) | transactions.filter(
            receiver__user__name__icontains=search_keyword) | transactions.filter(
            amount__icontains=search_keyword) | transactions.filter(
            created_at__icontains=search_keyword)

    # Serialize the transaction data
    serializer = TransactionSerializer(transactions, many=True)

    return Response({
        "status": True,
        "transactions": serializer.data
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transaction_count(request):
    period = request.query_params.get('time', 'all')  # Get the time period from query parameters

    # Get the current time
    now = timezone.now()

    # Calculate the start date based on the period
    if period == 'day':
        start_date = now - timedelta(days=1)
    elif period == 'week':
        start_date = now - timedelta(weeks=1)
    elif period == 'month':
        start_date = now - timedelta(weeks=4)  # Approximate month as 4 weeks
    elif period == 'year':
        start_date = now - timedelta(days=365)  # Approximate year as 365 days
    elif period == 'all':
        start_date = None  # No filtering for 'all'
    else:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        })

    # Filter transactions based on the start_date
    if start_date:
        transactions = Transaction.objects.filter(created_at=start_date)
    else:
        transactions = Transaction.objects.all()

    total_amount = transactions.aggregate(total_amount=Sum('amount'))
    total_sum = total_amount.get('total_amount', 0) or 0

    return Response({
        "status": True,
        "data": {
            "count": total_sum
        }
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_transaction_history(request):
    search = request.query_params.get('search', '').strip()

    # Fetch all transactions
    transactions = Transaction.objects.all()

    # Filter transactions based on search term
    if search:
        transactions = transactions.filter(
            sender__user__name__icontains=search) | transactions.filter(
            receiver__user__name__icontains=search) | transactions.filter(
            amount__icontains=search) | transactions.filter(
            created_at__icontains=search)

    # Sort transactions by created_at timestamp
    transactions = transactions.order_by('-created_at')

    # Prepare response data
    transaction_history = []
    for idx, transaction in enumerate(transactions, start=1):
        sender_name = transaction.sender.user.name
        receiver_name = transaction.receiver.user.name
        amount = transaction.amount
        formatted_date = transaction.created_at.strftime('%d %b %Y, %H:%M:%S')

        transaction_history.append({
            "id": transaction.id,  # Include transaction ID
            "index": idx,
            "sender_name": sender_name,
            "amount": amount,
            "receiver_name": receiver_name,
            "date": formatted_date,
        })

    return Response({
        "status": True,
        "transactions": transaction_history
    }, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_transaction_delete(request, transaction_id):
    # Fetch the transaction by its ID
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # Delete the transaction
    transaction.delete()

    return Response({
        "status": True,
        "message": "Transaction deleted successfully"
    }, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transaction_growth(request, period):
    try:
        current_start, previous_start = get_time_range(period)
        now = timezone.now()

        current_period_amount = Transaction.objects.filter(created_at__range=(current_start, now)).aggregate(Sum('amount'))['amount__sum'] or 0
        previous_period_amount = Transaction.objects.filter(created_at__range=(previous_start, current_start)).aggregate(Sum('amount'))['amount__sum'] or 0

        if previous_period_amount == 0:
            growth_percentage = 100.0 if current_period_amount > 0 else 0.0
        else:
            growth_percentage = ((current_period_amount - previous_period_amount) / previous_period_amount) * 100

        growth_percentage = f"{growth_percentage:.2f}"
        return Response({
            'status': True,
            'current': current_period_amount,
            'previous': previous_period_amount,
            'growth': growth_percentage
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transaction_monthly_summary(request):
    try:
        month_names, transaction_sums = get_six_month_transaction()

        return Response({
            'status': True,
            'y-axis': month_names,
            'x-axis': transaction_sums,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def debit_card_transaction_sum(request, period):
    now = timezone.now()

    def get_sum_and_previous_sum(period):
        if period == 'day':
            start_date = now - timedelta(days=1)
            previous_start_date = now - timedelta(days=2)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
            previous_start_date = now - timedelta(weeks=2)
        elif period == 'month':
            start_date = now - timedelta(weeks=4)  # Approximate month as 4 weeks
            previous_start_date = now - timedelta(weeks=8)  # Approximate previous month as 8 weeks
        elif period == 'year':
            start_date = now - timedelta(days=365)
            previous_start_date = now - timedelta(days=730)  # Approximate previous year as 730 days
        elif period == 'all':
            start_date = None
            previous_start_date = None
        else:
            return None, None

        # Filter transactions based on the start_date and type (debit card)
        if start_date:
            current_transactions = Transaction.objects.filter(created_at__gte=start_date, type=Transaction.TransactionType.DEBIT_CARD)
            previous_transactions = Transaction.objects.filter(created_at__gte=previous_start_date, created_at__lt=start_date, type=Transaction.TransactionType.DEBIT_CARD)
        else:
            current_transactions = Transaction.objects.filter(type=Transaction.TransactionType.DEBIT_CARD)
            previous_transactions = Transaction.objects.none()  # No previous data if period is 'all'

        current_sum = current_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0
        previous_sum = previous_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0

        return current_sum, previous_sum

    current_sum, previous_sum = get_sum_and_previous_sum(period)

    if current_sum is None:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        }, status=400)

    # Calculate growth percentage
    if previous_sum == 0:
        growth_percentage = 0 if current_sum == 0 else 100
    else:
        growth_percentage = ((current_sum - previous_sum) / previous_sum) * 100

    return Response({
        "status": True,
        "data": {
            "current": current_sum,
            "previous": previous_sum,
            "growth": growth_percentage
        }
    }, status=200)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def credit_card_transaction_count(request, period):
    now = timezone.now()

    def get_sum_and_previous_sum(period):
        if period == 'day':
            start_date = now - timedelta(days=1)
            previous_start_date = now - timedelta(days=2)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
            previous_start_date = now - timedelta(weeks=2)
        elif period == 'month':
            start_date = now - timedelta(weeks=4)  # Approximate month as 4 weeks
            previous_start_date = now - timedelta(weeks=8)  # Approximate previous month as 8 weeks
        elif period == 'year':
            start_date = now - timedelta(days=365)
            previous_start_date = now - timedelta(days=730)  # Approximate previous year as 730 days
        elif period == 'all':
            start_date = None
            previous_start_date = None
        else:
            return None, None

        # Filter transactions based on the start_date and type (credit card)
        if start_date:
            current_transactions = Transaction.objects.filter(created_at__gte=start_date, type=Transaction.TransactionType.CREDIT_CARD)
            previous_transactions = Transaction.objects.filter(created_at__gte=previous_start_date, created_at__lt=start_date, type=Transaction.TransactionType.CREDIT_CARD)
        else:
            current_transactions = Transaction.objects.filter(type=Transaction.TransactionType.CREDIT_CARD)
            previous_transactions = Transaction.objects.none()  # No previous data if period is 'all'

        current_sum = current_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0
        previous_sum = previous_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0

        return current_sum, previous_sum

    current_sum, previous_sum = get_sum_and_previous_sum(period)

    if current_sum is None:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        }, status=400)

    # Calculate growth percentage
    if previous_sum == 0:
        growth_percentage = 0 if current_sum == 0 else 100
    else:
        growth_percentage = ((current_sum - previous_sum) / previous_sum) * 100

    return Response({
        "status": True,
        "data": {
            "current": current_sum,
            "previous_sum": previous_sum,
            "growth": growth_percentage
        }
    }, status=200)