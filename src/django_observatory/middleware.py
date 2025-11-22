"""Middleware for Django Observatory to capture requests"""
import time
from django.utils import timezone
from .models import Request


class ObservatoryMiddleware:
    """
    Middleware to capture all HTTP requests and responses
    for monitoring in the Observatory dashboard
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip observatory's own requests to avoid infinite loop
        if request.path.startswith('/observatory/'):
            return self.get_response(request)
        
        # Create a pending request record
        start_time = time.time()
        
        request_record = Request.objects.create(
            method=request.method,
            path=request.path,
            query_params=request.GET.urlencode() if request.GET else '',
            status=Request.STATUS_PENDING
        )
        
        # Process the request
        response = self.get_response(request)
        
        # Update the request record with response information
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        request_record.status_code = response.status_code
        request_record.duration = duration_ms
        request_record.status = Request.STATUS_COMPLETED
        request_record.save()
        
        return response
