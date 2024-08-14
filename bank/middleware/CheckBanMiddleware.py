from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class CheckBanMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_ban:
            return JsonResponse({'status':False,'message': 'Your account is banned.'})
        # If the user is not banned, the request will proceed
        
