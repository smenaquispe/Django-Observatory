"""Middleware for Django Observatory to capture requests"""
import time
import json
from django.utils import timezone
from django.urls import resolve
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
        
        # Capture request information
        start_time = time.time()
        
        # Get request headers
        request_headers = {
            key: value for key, value in request.META.items()
            if key.startswith('HTTP_') or key in ['CONTENT_TYPE', 'CONTENT_LENGTH']
        }
        
        # Get request body
        request_body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                request_body = request.body.decode('utf-8')
            except:
                request_body = '[Binary data or unable to decode]'
        
        # Get view name
        view_name = None
        try:
            resolved = resolve(request.path)
            view_name = f"{resolved.view_name}"
            if resolved.func.__module__:
                view_name = f"{resolved.func.__module__}.{resolved.func.__name__}"
        except:
            pass
        
        # Create a pending request record
        request_record = Request.objects.create(
            method=request.method,
            path=request.path,
            query_params=request.GET.urlencode() if request.GET else '',
            request_headers=json.dumps(request_headers),
            request_body=request_body,
            view_name=view_name,
            status=Request.STATUS_PENDING
        )
        
        # Process the request
        response = self.get_response(request)
        
        # Capture response information
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Get response headers
        response_headers = dict(response.items()) if hasattr(response, 'items') else {}
        
        # Get response body
        response_body = None
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')
                # Limit response body size to avoid huge database entries
                if len(content) > 100000:  # 100KB limit
                    response_body = content[:100000] + '\n\n[... Response truncated ...]'
                else:
                    response_body = content
        except:
            response_body = '[Binary data or unable to decode]'
        
        # Update the request record with response information
        request_record.status_code = response.status_code
        request_record.duration = duration_ms
        request_record.status = Request.STATUS_COMPLETED
        request_record.response_headers = json.dumps(response_headers)
        request_record.response_body = response_body
        request_record.save()
        
        return response
