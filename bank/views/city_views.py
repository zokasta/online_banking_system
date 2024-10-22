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
def city_list(request):
    try:
        # Get the search parameter from the request, default to an empty string if not provided
        search_query = request.data.get('search', '').strip()

        # Fetch all cities or filter by city name or state name based on the search query
        if search_query:
            city = City.objects.filter(
                name__icontains=search_query
            ) | City.objects.filter(
                state__name__icontains=search_query  # Search for cities where the state's name contains the search query
            )
        else:
            city = City.objects.all()

        # Serialize the city data with the related state info, adding an index
        serializer = CitySerializer(city, many=True)  # many=True is important to serialize multiple objects
        city_data = [
            {
                "index": idx + 1,  # Add index starting from 1
                "city_name": c.name,
                "state_name": c.state.name,  # Access the related state's name
            } for idx, c in enumerate(city)
        ]

        return Response({"status": True, "message": "Cities fetched successfully", "data": city_data})

    except Exception as e:
        return Response({"status": False, "message": f"An error occurred: {str(e)}"})



# @api_view(['PUT'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated, IsAdminUserType])
# def cityUpdate(request):
 


@api_view(['GET'])
def cities_by_state(request, state_id):
    try:
        state = State.objects.get(id=state_id)
    except State.DoesNotExist:
        return Response({"status": False, "message": "State not found."})

    cities = City.objects.filter(state=state)
    serializer = CitySerializer(cities, many=True)
    return Response({"status": True, "data": serializer.data, "message": f"Cities in state {state.name}."})



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])  # Restrict this API to only admin users
def create_city(request):
    try:
        # Ensure state_id is an integer before passing to the serializer
        data = request.data.copy()
        state_id = data.get('state_id', None)
        
        if state_id is not None:
            try:
                data['state_id'] = int(state_id)
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid state_id. It must be an integer."
                })

        serializer = CitySerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "City created successfully",
                "data": serializer.data
            })
        else:
            return Response({
                "status": False,
                "message": "City creation failed",
                "errors": serializer.errors
            })

    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        })


