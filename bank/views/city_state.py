from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import State, City
from ..serializers import StateSerializer, CitySerializer

@api_view(['GET', 'POST'])
def state_list_create(request):
    if request.method == 'GET':
        states = State.objects.all()
        serializer = StateSerializer(states, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = StateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "data": serializer.data, "message": "State created successfully."})
        return Response({"status": False, "message": "State creation failed.", "errors": serializer.errors})

@api_view(['GET', 'PUT', 'DELETE'])
def state_detail(request, id):
    try:
        state = State.objects.get(id=id)
    except State.DoesNotExist:
        return Response({"status": False, "message": "State not found."})

    if request.method == 'GET':
        serializer = StateSerializer(state)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = StateSerializer(state, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "data": serializer.data, "message": "State updated successfully."})
        return Response({"status": False, "message": "State update failed.", "errors": serializer.errors})

    elif request.method == 'DELETE':
        state.delete()
        return Response({"status": True, "message": "State deleted successfully."})

@api_view(['GET', 'POST'])
def city_list_create(request):
    if request.method == 'GET':
        cities = City.objects.all()
        serializer = CitySerializer(cities, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "data": serializer.data, "message": "City created successfully."})
        return Response({"status": False, "message": "City creation failed.", "errors": serializer.errors})

@api_view(['GET'])
def cities_by_state(request, state_id):
    try:
        state = State.objects.get(id=state_id)
    except State.DoesNotExist:
        return Response({"status": False, "message": "State not found."})

    cities = City.objects.filter(state=state)
    serializer = CitySerializer(cities, many=True)
    return Response({"status": True, "data": serializer.data, "message": f"Cities in state {state.name}."})

@api_view(['GET', 'PUT', 'DELETE'])
def city_detail(request, id):
    try:
        city = City.objects.get(id=id)
    except City.DoesNotExist:
        return Response({"status": False, "message": "City not found."})

    if request.method == 'GET':
        serializer = CitySerializer(city)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CitySerializer(city, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "data": serializer.data, "message": "City updated successfully."})
        return Response({"status": False, "message": "City update failed.", "errors": serializer.errors})

    elif request.method == 'DELETE':
        city.delete()
        return Response({"status": True, "message": "City deleted successfully."})
