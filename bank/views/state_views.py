from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import State, City
from ..serializers import StateSerializer, CitySerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from ..permissions import IsAdminUserType
from rest_framework import status


@api_view(['GET'])
def state_list(request):
    try:
        search_query = request.data.get('search', '').strip()

        if search_query:
            states = State.objects.filter(name__icontains=search_query)
        else:
            states = State.objects.all()

        serializer = StateSerializer(states, many=True)  # Set many=True for serializing multiple objects
        return Response({"status": True, "data": serializer.data, "message": "States fetched successfully."})
    except Exception as e:
        return Response({"status": False, "message": f"An error occurred: {str(e)}"})



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
@permission_classes([IsAuthenticated, IsAdminUserType]) 
def create_state(request):
    try:
        # Deserialize the request data
        serializer = StateSerializer(data=request.data)

        # Validate and save the state data
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "State created successfully",
                "data": serializer.data
            })
        else:
            return Response({
                "status": False,
                "message": "State creation failed",
                "errors": serializer.errors
            })

    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        })



@api_view(['PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def edit_state(request, id):
    try:
        state = State.objects.get(id=id)

        serializer = StateSerializer(state, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "State updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": False,
                "message": "State update failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except State.DoesNotExist:
        return Response({
            "status": False,
            "message": "State not found."
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUserType])
def delete_state(request, id):
    try:
        state = State.objects.get(id=id)
        
        state.delete()
        return Response({
            "status": True,
            "message": "State deleted successfully."
        }, status=status.HTTP_200_OK)

    except State.DoesNotExist:
        return Response({
            "status": False,
            "message": "State not found."
        }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







