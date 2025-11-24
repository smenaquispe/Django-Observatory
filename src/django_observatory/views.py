"""Views for Django Observatory dashboard"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.test import Client as TestClient
from .models import Request
import json
import json


def dashboard_view(request):
    """
    Main dashboard view that displays the Observatory interface
    with three tabs: Requests, Logs, and Jobs
    """
    active_tab = request.GET.get('tab', 'requests')
    
    context = {
        'active_tab': active_tab
    }
    
    # If viewing requests tab, fetch recent requests
    if active_tab == 'requests':
        context['requests'] = Request.objects.all()[:50]  # Last 50 requests
    
    return render(request, 'django_observatory/dashboard.html', context)


def request_detail_view(request, request_id):
    """
    Detailed view of a single HTTP request showing complete
    request/response information.
    """
    req = get_object_or_404(Request, id=request_id)
    
    # Parse JSON data for better display
    request_headers = {}
    response_headers = {}
    request_body_parsed = None
    response_body_parsed = None
    
    # Parse headers
    try:
        if req.request_headers:
            request_headers = json.loads(req.request_headers)
    except:
        pass
    
    try:
        if req.response_headers:
            response_headers = json.loads(req.response_headers)
    except:
        pass
    
    # Try to parse request body as JSON
    if req.request_body:
        try:
            request_body_parsed = json.loads(req.request_body)
        except:
            request_body_parsed = req.request_body
    
    # Try to parse response body as JSON
    if req.response_body:
        try:
            response_body_parsed = json.loads(req.response_body)
        except:
            response_body_parsed = req.response_body
    
    context = {
        'req': req,
        'request_headers': request_headers,
        'response_headers': response_headers,
        'request_body_parsed': request_body_parsed,
        'response_body_parsed': response_body_parsed,
    }
    
    return render(request, 'django_observatory/request_detail.html', context)


@require_GET
def api_requests_list(request):
    """
    API endpoint to fetch requests for real-time updates.
    Returns JSON data with request information.
    """
    # Get optional timestamp parameter for filtering
    since_id = request.GET.get('since_id', None)
    limit = int(request.GET.get('limit', 50))
    
    # Query requests
    requests_query = Request.objects.all()
    
    # Filter by ID if since_id is provided
    if since_id:
        try:
            requests_query = requests_query.filter(id__gt=int(since_id))
        except (ValueError, TypeError):
            pass
    
    # Limit results
    requests_list = requests_query[:limit]
    
    # Serialize requests to JSON
    data = {
        'count': requests_query.count(),
        'total': Request.objects.count(),
        'requests': [
            {
                'id': req.id,
                'method': req.method,
                'path': req.path,
                'query_params': req.query_params or '',
                'status_code': req.status_code,
                'status': req.status,
                'status_category': req.get_status_category(),
                'timestamp': req.timestamp.isoformat(),
                'duration': req.duration,
            }
            for req in requests_list
        ]
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_POST
def api_reprocess_request(request, request_id):
    """
    Reprocess a captured request with optionally modified payload.
    """
    try:
        # Get the original request
        original_request = Request.objects.get(id=request_id)
        
        # Parse the incoming JSON data
        data = json.loads(request.body.decode('utf-8'))
        modified_body = data.get('request_body', original_request.request_body)
        
        # Create a test client to replay the request
        client = TestClient()
        
        # Prepare the request parameters
        path = original_request.path
        method = original_request.method.lower()
        
        # Parse headers from the original request
        headers = {}
        if original_request.request_headers:
            try:
                headers = json.loads(original_request.request_headers)
            except (json.JSONDecodeError, TypeError):
                headers = {}
        
        # Prepare kwargs for the test client request
        kwargs = {}
        if modified_body:
            kwargs['data'] = modified_body
            kwargs['content_type'] = headers.get('Content-Type', 'application/json')
        
        # Make the request using the test client
        if method == 'get':
            response = client.get(path, **kwargs)
        elif method == 'post':
            response = client.post(path, **kwargs)
        elif method == 'put':
            response = client.put(path, **kwargs)
        elif method == 'patch':
            response = client.patch(path, **kwargs)
        elif method == 'delete':
            response = client.delete(path, **kwargs)
        else:
            return JsonResponse({'error': f'Unsupported method: {method}'}, status=400)
        
        # Find the newly created request (most recent one with same path and method)
        new_request = Request.objects.filter(
            path=path,
            method=original_request.method
        ).order_by('-timestamp').first()
        
        if new_request and new_request.id != request_id:
            return JsonResponse({
                'request_id': new_request.id,
                'status': 'processing'
            })
        else:
            return JsonResponse({'error': 'Failed to create new request'}, status=500)
            
    except Request.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
