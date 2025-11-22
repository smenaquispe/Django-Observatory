"""Views for Django Observatory dashboard"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Request


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
