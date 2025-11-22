"""Views for Django Observatory dashboard"""
from django.shortcuts import render


def dashboard_view(request):
    """
    Main dashboard view that displays the Observatory interface
    with three tabs: Requests, Logs, and Jobs
    """
    context = {
        'active_tab': request.GET.get('tab', 'requests')
    }
    return render(request, 'django_observatory/dashboard.html', context)
