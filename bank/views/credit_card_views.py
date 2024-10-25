from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from ..models import CreditCard, Account
from ..permissions import IsAdminUserType, IsUserType
from rest_framework import status
from django.db.models import Sum, Count
from ..serializers import CreditCardSerializer


from rest_framework.decorators import api_view,authentication_classes,permission_classes
from .functions import generate_card_number,generate_expiration_date,generate_cvv,get_time_range



@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def apply_for_credit_card(request):
    user = request.user 

    if CreditCard.objects.filter(user=user).exists():
        return Response(
            {"status": False, "message": "You already send the application."}
        )
        
    card_number = generate_card_number()
    expiration_date = (
        generate_expiration_date()
    )
    cvv = generate_cvv()

    try:
        new_credit_card = CreditCard.objects.create(
            user=user,
            card_number=card_number,
            expiration_date=expiration_date,
            cvv=cvv,
            limit_use=30000,
            status="pending",
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        return Response(
            {"status": True, "message": "Credit card application successful."},
            status=201,
        )

    except Exception as e:
        return Response(
            {"status": False, "message": f"Failed to create credit card: {str(e)}"}
        )



@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def get_credit_card_list(request):

    search = request.query_params.get("search", "").strip()

    credit_cards = CreditCard.objects.filter(status="confirm")

    if search:
        credit_cards = credit_cards.filter(card_number__icontains=search)

    credit_card_list = []
    for idx, credit_card in enumerate(credit_cards, start=1):
        credit_card_list.append(
            {
                "index": idx,
                "id": credit_card.id,
                "card_number": credit_card.card_number,
                "expiration_date": credit_card.expiration_date,
                "cvv": credit_card.cvv,
                "status": credit_card.status,
                "is_freeze": credit_card.is_freeze,
                "limit_use": credit_card.limit_use,
                "created_at": credit_card.created_at.strftime("%d %b %Y, %H:%M:%S"),
                "updated_at": credit_card.updated_at.strftime("%d %b %Y, %H:%M:%S"),
            }
        )

    return Response(
        {"status": True, "data": {"credit_cards": credit_card_list}}, status=200
    )



@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def get_credit_card_usage(request):
    user_id = request.user.id
    try:
        credit_card = CreditCard.objects.get(user_id=user_id)
        left_limit = credit_card.limit_use - credit_card.used
        return Response({"status": True, "data": left_limit}, status=200)
    except CreditCard.DoesNotExist:
        return Response(
            {"status": False, "message": "No credit card found for this user."}
        )
    except Exception as e:
        return Response({"status": False, "message": f"An error occurred: {str(e)}"})



@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsUserType])
def pay_credit_card_bills(request):
    user_id = request.user.id

    try:
        mpin = request.data.get("mpin")
        account = Account.objects.get(user_id=user_id)
        credit_card = CreditCard.objects.get(user_id=user_id)
        user_mpin = request.user.mpin

        if mpin != user_mpin:
            return Response({"status": False, "message": "MPIN is not a valid"})

        payment_amount = credit_card.used

        if account.balance < payment_amount:
            return Response(
                {"status": False, "message": "Insufficient balance in your account."}
            )

        if credit_card.used == 0:
            return Response(
                {
                    "status": False,
                    "message": "No outstanding balance on your credit card.",
                }
            )

        account.balance -= payment_amount
        account.save()

        try:
            receiving_account = Account.objects.get(id=1)
            receiving_account.balance += payment_amount
            receiving_account.save()
        except Account.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Receiving account with ID 1 does not exist.",
                }
            )

        credit_card.used = 0
        credit_card.updated_at = timezone.now()
        credit_card.save()

        return Response(
            {
                "status": True,
                "message": "Payment successful.",
                "user_account_balance": account.balance,
                "paid_amount": payment_amount,
            },
            status=200,
        )

    except Account.DoesNotExist:
        return Response({"status": False, "message": "User account not found."})

    except CreditCard.DoesNotExist:
        return Response(
            {"status": False, "message": "No credit card found for this user."}
        )

    except Exception as e:
        return Response({"status": False, "message": f"An error occurred: {str(e)}"})



@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def get_pending_credit_card_applications(request):
    try:
        pending_credit_cards = CreditCard.objects.filter(status="pending")

        pending_credit_card_list = []
        for idx, credit_card in enumerate(pending_credit_cards, start=1):
            user = credit_card.user

            pending_credit_card_list.append(
                {
                    "index": idx,
                    "id": credit_card.id,
                    "user_name": user.name,
                    "user_phone": user.phone,
                    "card_number": credit_card.card_number,
                    "expiration_date": credit_card.expiration_date,
                    "cvv": credit_card.cvv,
                    "limit_use": credit_card.limit_use,
                    "created_at": credit_card.created_at.strftime("%d %b %Y, %H:%M:%S"),
                    "updated_at": credit_card.updated_at.strftime("%d %b %Y, %H:%M:%S"),
                }
            )

        return Response(
            {
                "status": True,
                "data": {"pending_credit_cards": pending_credit_card_list},
            },
            status=200,
        )

    except Exception as e:
        return Response(
            {"status": False, "message": f"An error occurred: {str(e)}"}, status=500
        )



@api_view(["PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def change_credit_card_status(request, credit_card_id):
    try:
        new_status = request.data.get("status")

        if not credit_card_id or not new_status:
            return Response(
                {
                    "status": False,
                    "message": "Credit card ID and new status are required.",
                }
            )

        allowed_statuses = ["pending", "approved", "rejected", "blocked"]
        if new_status not in allowed_statuses:
            return Response({"status": False, "message": "Invalid status value."})

        try:
            credit_card = CreditCard.objects.get(id=credit_card_id)
        except CreditCard.DoesNotExist:
            return Response({"status": False, "message": "Credit card not found."})

        credit_card.status = new_status
        credit_card.updated_at = timezone.now()
        credit_card.save()

        return Response(
            {
                "status": True,
                "message": f"Credit card status updated to {new_status}.",
                "new_status": new_status,
            },
            status=200,
        )

    except Exception as e:
        return Response(
            {"status": False, "message": f"An error occurred: {str(e)}"}, status=500
        )



@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def credit_card_statistics(request, period):
    try:
        current_start, previous_start = get_time_range(period)
        now = timezone.now()

        current_period_stats = CreditCard.objects.filter(
            created_at__range=(current_start, now)
        ).aggregate(total_created=Count("id"))

        previous_period_stats = CreditCard.objects.filter(
            created_at__range=(previous_start, current_start)
        ).aggregate(total_created=Count("id"))

        if previous_period_stats["total_created"] == 0:
            growth_percentage = (
                100.0 if current_period_stats["total_created"] > 0 else 0.0
            )
        else:
            growth_percentage = (
                (
                    current_period_stats["total_created"]
                    - previous_period_stats["total_created"]
                )
                / previous_period_stats["total_created"]
            ) * 100

        return Response(
            {
                "status": True,
                "data": {
                    "current": current_period_stats["total_created"],
                    "previous": previous_period_stats["total_created"],
                    "growth_percentage": growth_percentage,
                },
            },
            status=status.HTTP_200_OK,
        )

    except ValueError as e:
        return Response(
            {"status": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        return Response(
            {"status": False, "message": "An error occurred: " + str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@api_view(["PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def edit_credit_card_details(request, credit_card_id):
    try:
        user = request.user

        try:
            credit_card = CreditCard.objects.get(id=credit_card_id, user=user)
        except CreditCard.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "Credit card not found or you do not have permission to edit this card.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        expiration_date = request.data.get("expiration_date")
        limit_use = request.data.get("limit_use")
        limit_use = int(limit_use)
        card_number = request.data.get("card_number")

        if expiration_date:
            try:
                credit_card.expiration_date = (
                    expiration_date
                )
            except ValueError:
                return Response(
                    {"status": False, "message": "Invalid expiration date format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if limit_use:
            if isinstance(limit_use, int) and limit_use > 0:
                credit_card.limit_use = limit_use
            else:
                return Response(
                    {"status": False, "message": "Limit must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if card_number:
            if (
                CreditCard.objects.filter(card_number=card_number)
                .exclude(id=credit_card.id)
                .exists()
            ):
                return Response(
                    {"status": False, "message": "This card number is already in use."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            credit_card.card_number = card_number
        credit_card.updated_at = timezone.now()
        credit_card.save()

        return Response(
            {
                "status": True,
                "message": "Credit card details updated successfully.",
                "data": {
                    "card_number": credit_card.card_number,
                    "expiration_date": credit_card.expiration_date,
                    "limit_use": credit_card.limit_use,
                    "updated_at": credit_card.updated_at.strftime("%d %b %Y, %H:%M:%S"),
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"status": False, "message": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@api_view(["PATCH"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def toggle_credit_card(request, credit_card_id):
    try:
        user = request.user
        freeze_status = request.data.get("status", None)

        if freeze_status == "none":
            freeze_status = False
        else:
            freeze_status = True

        if freeze_status is None:
            return Response(
                {
                    "status": False,
                    "message": "Freeze status is required (True or False).",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            credit_card = CreditCard.objects.get(id=credit_card_id)
        except CreditCard.DoesNotExist:
            return Response(
                {"status": False, "message": "Credit card not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if credit_card.is_freeze == freeze_status:
            return Response(
                {
                    "status": False,
                    "message": f"Credit card is already {'frozen' if freeze_status else 'unfrozen'}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        credit_card.is_freeze = freeze_status
        credit_card.updated_at = timezone.now()
        credit_card.save()

        return Response(
            {
                "status": True,
                "message": f"Credit card has been {'frozen' if freeze_status else 'unfrozen'} successfully.",
                "is_freeze": credit_card.is_freeze,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"status": False, "message": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def check_credit_card(request):
    try:
        credit_card = CreditCard.objects.filter(user=request.user).first()

        if credit_card:
            serializer = CreditCardSerializer(credit_card)
            return Response(
                {
                    "status": True,
                    "message": "Credit card found",
                    "credit_card_request": credit_card.status,
                    "data" : serializer.data
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "status": False,
                    "message": "No credit card found for this user.",
                    "credit_card_request": "NoCreditCardFound"
                },
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        return Response(
            {
                "status": False,
                "message": f"An error occurred: {str(e)}",
                "credit_card_request": "NoCreditCardFound",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )







