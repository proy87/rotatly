from django.shortcuts import redirect

class RedirectToWWWMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()  # now works correctly behind proxy
        if host == 'rotatly.com':
            url = request.build_absolute_uri().replace('://rotatly.com', '://www.rotatly.com')
            return redirect(url, permanent=True)
        return self.get_response(request)