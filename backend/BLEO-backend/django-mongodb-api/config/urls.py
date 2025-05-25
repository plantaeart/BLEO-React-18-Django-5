from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse

def api_root(request):
    """View function for the root URL that returns API information"""
    return JsonResponse({
        "name": "BLEO API",
        "version": "1.0",
        "endpoints": {
            "users": "/api/users/",
            "links": "/api/links/",
            "messages": "/api/messages/"
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # Add root URL pattern that shows API info
    path('', api_root, name='api-root'),
]