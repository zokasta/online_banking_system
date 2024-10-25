from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import State, City
from ..serializers import StateSerializer, CitySerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsAdminUserType
from rest_framework import status


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
        search_query = request.data.get('search', '').strip()

        if search_query:
            city = City.objects.filter(
                name__icontains=search_query
            ) | City.objects.filter(
                state__name__icontains=search_query
            )
        else:
            city = City.objects.all()

        serializer = CitySerializer(city, many=True)
        city_data = [
            {
                "index": idx + 1,
                "city_name": c.name,
                "id": c.id,
                "state_name": c.state.name,
            } for idx, c in enumerate(city)
        ]

        return Response({"status": True, "message": "Cities fetched successfully", "data": city_data})

    except Exception as e:
        return Response({"status": False, "message": f"An error occurred: {str(e)}"})



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
@permission_classes([IsAuthenticated, IsAdminUserType])
def create_city(request):
    try:
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



@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def city_delete(request, id):
    try:
        city = City.objects.get(id=id)
        city.delete()
        return Response({
            "status": True,
            "message": "City deleted successfully."
        }, status=status.HTTP_200_OK)
    except City.DoesNotExist:
        return Response({
            "status": False,
            "message": "City not found."
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def city_edit(request, id):
    try:
        city = City.objects.get(id=id)

        if 'city_name' in request.data:
            city.name = request.data['city_name']

        state_id = request.data.get('state_name')
        if state_id:
            try:
                state = State.objects.get(id=state_id)
                city.state = state 
            except State.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "State not found."
                }, status=status.HTTP_404_NOT_FOUND)

        city.save()

        serializer = CitySerializer(city)

        return Response({
            "status": True,
            "message": "City updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    except City.DoesNotExist:
        return Response({
            "status": False,
            "message": "City not found."
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








