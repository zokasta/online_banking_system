"""
# Todo: I think we should add 2% charge on Credit Card
# Status: Pending

"""

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Account, Transaction, CreditCard
from ..serializers import TransactionSerializer, AccountSerializer
from rest_framework import status
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db import transaction as db_transaction
from django.db.models import Q
from .functions import get_time_range,get_six_month_transaction,get_six_month_credit_card_transactions,get_six_month_debit_card_transactions, get_six_month_credit_card_transactions_for_admin
from .functions import get_six_month_credit_card_transactions_for_admin,get_six_month_rolled_back_transactions
from ..permissions import IsAdminUserType, IsUserType
import logging
logger = logging.getLogger(__name__)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def create_transaction(request):
    sender = request.user
    amount = request.data.get('amount', 0)
    upi_id = request.data.get('upi_id')
    mpin = request.data.get('mpin')
    transaction_type = request.data.get('type', 'DC').upper()

    if not isinstance(amount, (int, float)) or amount <= 0:
        return Response({
            "status": False,
            "message": "Invalid amount. Amount must be greater than zero."
        }, status=status.HTTP_400_BAD_REQUEST)

    if sender.mpin != mpin:
        return Response({
            "status": False,
            "message": "Invalid MPIN",
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        with db_transaction.atomic():
            sender_account = get_object_or_404(Account.objects.select_for_update(), user=sender)

            if transaction_type == 'CC':
                credit_card = get_object_or_404(CreditCard, user=sender, is_freeze=False)
                available_credit = credit_card.limit_use - credit_card.used

                if available_credit < amount:
                    return Response({
                        "status": False,
                        "message": "Insufficient credit card balance"
                    }, status=status.HTTP_400_BAD_REQUEST)

                credit_card.used += amount
                credit_card.save()

            receiver_account = Account.objects.filter(upi_id=upi_id).first()

            if transaction_type != 'CC':
                if sender_account.balance < amount:
                    return Response({
                        "status": False,
                        "message": "Insufficient funds"
                    }, status=status.HTTP_400_BAD_REQUEST)

                sender_account.balance -= amount
                sender_account.save()

            receiver_account.balance += amount
            receiver_account.save()

            transaction_data = {
                'sender': sender_account.id,
                'receiver': receiver_account.id,
                'amount': amount,
                'type': transaction_type,
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
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Transaction error: {str(e)}")
        return Response({
            'status': False,
            'message': 'Transaction failed, all changes rolled back.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def see_balance(request):
    account = get_object_or_404(Account, user=request.user)
    serializer = AccountSerializer(account)
    return Response({
        "status": True,
        "balance": serializer.data['balance']
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def transaction_history(request):
    type = request.query_params.get('type')
    account = get_object_or_404(Account, user=request.user)
    search = request.query_params.get('search', '').strip()

    sent_transactions = Transaction.objects.filter(sender=account,type=type)
    received_transactions = Transaction.objects.filter(receiver=account, type=type)

    transactions_dict = {}

    for transaction in sent_transactions:
        transactions_dict[transaction.pk] = {
            "transaction": transaction,
            "status_info": 'Debit'
        }

    for transaction in received_transactions:
        if transaction.pk not in transactions_dict:
            transactions_dict[transaction.pk] = {
                "transaction": transaction,
                "status_info": 'Credit'
            }
        else:
            transactions_dict[transaction.pk]["status_info"] = 'Self Transfer'

    transactions = list(transactions_dict.values())

    transactions.sort(key=lambda t: t["transaction"].created_at, reverse=True)

    filtered_transactions = []
    for idx, trans_dict in enumerate(transactions, start=1):
        transaction = trans_dict["transaction"]
        status_info = trans_dict["status_info"]

        if transaction.sender == account:
            name = transaction.receiver.user.name
        else:
            name = transaction.sender.user.name

        formatted_timestamp = transaction.created_at.strftime('%d %b %Y, %H:%M:%S')

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
@permission_classes([IsAuthenticated, IsUserType])
def show_transaction(request):
    user = request.user
    account = get_object_or_404(Account, user=user)

    search_keyword = request.data.get('search', '')

    transactions = Transaction.objects.filter(sender=account) | Transaction.objects.filter(receiver=account)

    
    if search_keyword:
        transactions = transactions.filter(
            sender__user__name__icontains=search_keyword) | transactions.filter(
            receiver__user__name__icontains=search_keyword) | transactions.filter(
            amount__icontains=search_keyword) | transactions.filter(
            created_at__icontains=search_keyword)

    serializer = TransactionSerializer(transactions, many=True)

    return Response({
        "status": True,
        "transactions": serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def transaction_count(request):
    period = request.query_params.get('time', 'all')

    now = timezone.now()

    if period == 'day':
        start_date = now - timedelta(days=1)
    elif period == 'week':
        start_date = now - timedelta(weeks=1)
    elif period == 'month':
        start_date = now - timedelta(weeks=4)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    elif period == 'all':
        start_date = None
    else:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        })

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
@permission_classes([IsAuthenticated, IsAdminUserType])
def admin_transaction_history(request):
    search = request.query_params.get('search', '').strip()

    transactions = Transaction.objects.all()

    if search:
        transactions = transactions.filter(
            sender__user__name__icontains=search) | transactions.filter(
            receiver__user__name__icontains=search) | transactions.filter(
            amount__icontains=search) | transactions.filter(
            created_at__icontains=search)

    transactions = transactions.order_by('-created_at')

    transaction_history = []
    for idx, transaction in enumerate(transactions, start=1):
        sender_name = transaction.sender.user.name
        receiver_name = transaction.receiver.user.name
        amount = transaction.amount
        is_rolled_back = transaction.is_rolled_back
        formatted_date = transaction.created_at.strftime('%d %b %Y, %H:%M:%S')

        transaction_history.append({
            "id": transaction.id,
            "index": idx,
            "sender_name": sender_name,
            "amount": amount,
            "receiver_name": receiver_name,
            "is_rolled_back": is_rolled_back,
            "date": formatted_date,
        })

    return Response({
        "status": True,
        "transactions": transaction_history
    }, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def admin_transaction_delete(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)

    transaction.delete()

    return Response({
        "status": True,
        "message": "Transaction deleted successfully"
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
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
            "data":{
                'current': current_period_amount,
                'previous': previous_period_amount,
                'growth': growth_percentage
            }
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
@permission_classes([IsAuthenticated, IsAdminUserType])
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
@permission_classes([IsAuthenticated, IsAdminUserType])
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
            start_date = now - timedelta(weeks=4)
            previous_start_date = now - timedelta(weeks=8)
        elif period == 'year':
            start_date = now - timedelta(days=365)
            previous_start_date = now - timedelta(days=730)
        elif period == 'all':
            start_date = None
            previous_start_date = None
        else:
            return None, None

        if start_date:
            current_transactions = Transaction.objects.filter(created_at__gte=start_date, type=Transaction.TransactionType.DEBIT_CARD)
            previous_transactions = Transaction.objects.filter(created_at__gte=previous_start_date, created_at__lt=start_date, type=Transaction.TransactionType.DEBIT_CARD)
        else:
            current_transactions = Transaction.objects.filter(type=Transaction.TransactionType.DEBIT_CARD)
            previous_transactions = Transaction.objects.none()

        current_sum = current_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0
        previous_sum = previous_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0

        return current_sum, previous_sum

    current_sum, previous_sum = get_sum_and_previous_sum(period)

    if current_sum is None:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        }, status=400)

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
@permission_classes([IsAuthenticated, IsAdminUserType])
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
            start_date = now - timedelta(weeks=4)
            previous_start_date = now - timedelta(weeks=8)
        elif period == 'year':
            start_date = now - timedelta(days=365)
            previous_start_date = now - timedelta(days=730)
        elif period == 'all':
            start_date = None
            previous_start_date = None
        else:
            return None, None

        if start_date:
            current_transactions = Transaction.objects.filter(created_at__gte=start_date, type=Transaction.TransactionType.CREDIT_CARD)
            previous_transactions = Transaction.objects.filter(created_at__gte=previous_start_date, created_at__lt=start_date, type=Transaction.TransactionType.CREDIT_CARD)
        else:
            current_transactions = Transaction.objects.filter(type=Transaction.TransactionType.CREDIT_CARD)
            previous_transactions = Transaction.objects.none()

        current_sum = current_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0
        previous_sum = previous_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0

        return current_sum, previous_sum

    current_sum, previous_sum = get_sum_and_previous_sum(period)

    if current_sum is None:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        }, status=400)

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



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def debit_card_transaction_sum_for_user(request, period):
    user_id = request.user.id
    now = timezone.now()

    def get_sum_and_previous_sum(period):
        if period == 'day':
            start_date = now - timedelta(days=1)
            previous_start_date = now - timedelta(days=2)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
            previous_start_date = now - timedelta(weeks=2)
        elif period == 'month':
            start_date = now - timedelta(weeks=4)
            previous_start_date = now - timedelta(weeks=8)
        elif period == 'year':
            start_date = now - timedelta(days=365)
            previous_start_date = now - timedelta(days=730)
        elif period == 'all':
            start_date = None
            previous_start_date = None
        else:
            return None, None

        if start_date:
            current_transactions = Transaction.objects.filter(
                created_at__gte=start_date,
                type=Transaction.TransactionType.DEBIT_CARD
            ).filter(
                (Q(sender_id=user_id) | Q(receiver_id=user_id))
            )

            previous_transactions = Transaction.objects.filter(
                created_at__gte=previous_start_date,
                created_at__lt=start_date,
                type=Transaction.TransactionType.DEBIT_CARD
            ).filter(
                (Q(sender_id=user_id) | Q(receiver_id=user_id))
            )
        else:
            current_transactions = Transaction.objects.filter(
                type=Transaction.TransactionType.DEBIT_CARD
            ).filter(
                (Q(sender_id=user_id) | Q(receiver_id=user_id))
            )
            previous_transactions = Transaction.objects.none()

        current_sum = current_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0
        previous_sum = previous_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0

        return current_sum, previous_sum

    current_sum, previous_sum = get_sum_and_previous_sum(period)

    if current_sum is None:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        }, status=400)

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
@permission_classes([IsAuthenticated, IsUserType])
def credit_card_transaction_count_for_user(request, period):
    user_id = request.user.id
    now = timezone.now()

    def get_sum_and_previous_sum(period):
        if period == 'day':
            start_date = now - timedelta(days=1)
            previous_start_date = now - timedelta(days=2)
        elif period == 'week':
            start_date = now - timedelta(weeks=1)
            previous_start_date = now - timedelta(weeks=2)
        elif period == 'month':
            start_date = now - timedelta(weeks=4)
            previous_start_date = now - timedelta(weeks=8)
        elif period == 'year':
            start_date = now - timedelta(days=365)
            previous_start_date = now - timedelta(days=730)
        elif period == 'all':
            start_date = None
            previous_start_date = None
        else:
            return None, None

        if start_date:
            current_transactions = Transaction.objects.filter(
                created_at__gte=start_date,
                type=Transaction.TransactionType.CREDIT_CARD
            ).filter(Q(sender_id=user_id) | Q(receiver_id=user_id))

            previous_transactions = Transaction.objects.filter(
                created_at__gte=previous_start_date,
                created_at__lt=start_date,
                type=Transaction.TransactionType.CREDIT_CARD
            ).filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
        else:
            current_transactions = Transaction.objects.filter(
                type=Transaction.TransactionType.CREDIT_CARD
            ).filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
            previous_transactions = Transaction.objects.none()

        current_sum = current_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0
        previous_sum = previous_transactions.aggregate(total_amount=Sum('amount')).get('total_amount', 0) or 0

        return current_sum, previous_sum

    current_sum, previous_sum = get_sum_and_previous_sum(period)

    if current_sum is None:
        return Response({
            "status": False,
            "message": "Invalid time period. Choose from 'day', 'week', 'month', 'year', 'all'."
        }, status=400)

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



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def credit_card_transaction_summary(request):
    user = request.user
    try:
        month_names, transaction_sums = get_six_month_credit_card_transactions(user)

        return Response({
            'status': True,
            'x-axis': {i: transaction_sums[i] for i in range(len(transaction_sums))},
            'y-axis': {i: month_names[i] for i in range(len(month_names))},
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def debit_card_transaction_summary(request):
    user = request.user
    try:
        month_names, transaction_sums = get_six_month_debit_card_transactions(user)

        return Response({
            'status': True,
            'x-axis': {i: transaction_sums[i] for i in range(len(transaction_sums))},
            'y-axis': {i: month_names[i] for i in range(len(month_names))},
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def rollback_transaction(request, transaction_id):
    try:
        transaction = get_object_or_404(Transaction, id=transaction_id, is_rolled_back=False)

        with db_transaction.atomic():
            sender_account = get_object_or_404(Account.objects.select_for_update(), id=transaction.sender.id)
            receiver_account = get_object_or_404(Account.objects.select_for_update(), id=transaction.receiver.id)

            if transaction.type == 'CC':
                credit_card = get_object_or_404(CreditCard, user=sender_account.user)

                # if credit_card.used < transaction.amount:
                #     return Response({
                #         "status": False,
                #         "message": "Credit card balance insufficient for rollback."
                #     })

                credit_card.used -= transaction.amount
                credit_card.save()

            if receiver_account.balance < transaction.amount:
                return Response({
                    "status": False,
                    "message": "Receiver balance insufficient for rollback."
                })

            sender_account.balance += transaction.amount
            receiver_account.balance -= transaction.amount

            sender_account.save()
            receiver_account.save()

            transaction.is_rolled_back = True
            transaction.save()

            return Response({
                'status': True,
                'message': 'Transaction successfully rolled back.'
            })

    except Exception as e:
        logger.error(f"Rollback error: {str(e)}")
        return Response({
            'status': False,
            'message': 'Transaction rollback failed, changes were not applied.'
        })



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def rollback_statistics(request, period):
    try:
        current_start, previous_start = get_time_range(period)
        now = timezone.now()

        current_period_rollbacks = Transaction.objects.filter(
            is_rolled_back=True, 
            created_at__range=(current_start, now)
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        previous_period_rollbacks = Transaction.objects.filter(
            is_rolled_back=True, 
            created_at__range=(previous_start, current_start)
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        if previous_period_rollbacks == 0:
            growth_percentage = 100.0 if current_period_rollbacks > 0 else 0.0
        else:
            growth_percentage = ((current_period_rollbacks - previous_period_rollbacks) / previous_period_rollbacks) * 100

        return Response({
            "status": True,
            "data": {
                'current': current_period_rollbacks,
                'previous': previous_period_rollbacks,
                'growth_percentage': growth_percentage
            }
        }, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'status': False,
            'message': 'An error occurred: ' + str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def transaction_monthly_summary_for_credit_card(request):
    try:
        month_names, transaction_sums = get_six_month_credit_card_transactions_for_admin(type = Transaction.TransactionType.CREDIT_CARD)

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
@permission_classes([IsAuthenticated, IsAdminUserType])
def transaction_monthly_summary_for_debit_card(request):
    try:
        month_names, transaction_sums = get_six_month_credit_card_transactions_for_admin(type = Transaction.TransactionType.DEBIT_CARD)

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
@permission_classes([IsAuthenticated, IsAdminUserType])
def transaction_monthly_summary_for_rolled_back(request):
    try:
        month_names, transaction_sums = get_six_month_rolled_back_transactions()

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






