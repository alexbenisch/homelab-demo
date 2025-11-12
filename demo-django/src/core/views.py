import os
import platform
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


def home(request):
    """Home page with basic info."""
    context = {
        'title': 'Demo Django App',
        'message': 'Welcome to your homelab Django application!',
    }
    return render(request, 'core/home.html', context)


@require_http_methods(["GET"])
def health(request):
    """Health check endpoint for Kubernetes."""
    return JsonResponse({'status': 'healthy'})


@require_http_methods(["GET"])
def ready(request):
    """Readiness probe endpoint for Kubernetes."""
    # You can add database checks here if needed
    return JsonResponse({'status': 'ready'})


@require_http_methods(["GET"])
def info(request):
    """System information endpoint."""
    return JsonResponse({
        'app': 'demo-django',
        'version': '0.1.0',
        'python_version': platform.python_version(),
        'hostname': os.environ.get('HOSTNAME', 'unknown'),
        'environment': os.environ.get('ENVIRONMENT', 'development'),
    })
