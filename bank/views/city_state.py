from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import State, City
from ..serializers import StateSerializer, CitySerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsAdminUserType


@api_view(['POST'])
def state_list_create(request):
    serializer = StateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": True, "data": serializer.data, "message": "State created successfully."})
    return Response({"status": False, "message": "State creation failed.", "errors": serializer.errors})



@api_view(['GET'])
def state_detail(request, id):
    try:
        state = State.objects.get(id=id)
        serializer = StateSerializer(state)
        return Response(serializer.data)
    except State.DoesNotExist:
        return Response({"status": False, "message": "State not found."})  



@api_view(['GET'])
def city_detail(request, id):
    try:
        city = City.objects.get(id=id)
        serializer = CitySerializer(city)
        return Response(serializer.data)
    except City.DoesNotExist:
        return Response({"status": False, "message": "City not found."})



@api_view(['GET'])
def cities_by_state(request, state_id):
    try:
        state = State.objects.get(id=state_id)
    except State.DoesNotExist:
        return Response({"status": False, "message": "State not found."})

    cities = City.objects.filter(state=state)
    serializer = CitySerializer(cities, many=True)
    return Response({"status": True, "data": serializer.data, "message": f"Cities in state {state.name}."})




