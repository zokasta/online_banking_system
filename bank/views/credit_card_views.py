from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from ..models import CreditCard
from .functions import generate_card_number, generate_expiration_date, generate_cvv


# @csrf_exempt  # Disable CSRF for this view
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def apply_for_credit_card(request):
    user = request.user  # Get the authenticated user

    # Check if the user already has a credit card
    if CreditCard.objects.filter(user=user).exists():
        return Response({'status': False, 'message': 'You already have a credit card.'})

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
            status='active',
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

        return Response({'status': True, 'message': 'Credit card application successful.'}, status=201)

    except Exception as e:
        return Response({'status': False, 'message': f'Failed to create credit card: {str(e)}'})
