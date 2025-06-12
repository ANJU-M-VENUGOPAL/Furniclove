from django.utils.deprecation import MiddlewareMixin

class EnsureUserProfileMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Your middleware logic here
        pass
