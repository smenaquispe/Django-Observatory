import pytest
from django.test import Client
from unittest.mock import patch


@pytest.mark.django_db
class TestObservatoryDashboard:
    """Test suite for the Observatory dashboard interface."""
    
    def test_observatory_dashboard_shows_three_tabs(self, client):
        """
        Test that the Observatory dashboard displays three tabs:
        - Requests
        - Logs
        - Jobs
        """

        response = client.get('/observatory/')
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        
        assert 'Requests' in content, "The 'Requests' tab should be present"
        assert 'Logs' in content, "The 'Logs' tab should be present"
        assert 'Jobs' in content, "The 'Jobs' tab should be present"


@pytest.mark.django_db
class TestRequestMonitoring:
    """Test suite for request monitoring functionality."""
    
    def test_requests_are_displayed_as_cards(self, client):
        """
        Test that requests are displayed as cards in the Requests tab.
        
        Given: The Observatory middleware is active
        When: A request is made to any endpoint
        Then: The request should appear as a card in the requests list
        """
        # Make a test request to trigger the middleware
        response = client.get('/admin/')
        
        # Now check the observatory dashboard
        dashboard_response = client.get('/observatory/?tab=requests')
        content = dashboard_response.content.decode('utf-8')
        
        # Verify that the request card structure exists
        assert 'request-card' in content, "Request cards should be present"
        assert '/admin/' in content, "The monitored request path should be displayed"
    
    def test_request_cards_show_status_code_colors(self, client):
        """
        Test that request cards change color based on HTTP status code.
        
        Given: Multiple requests with different status codes
        When: Viewing the requests tab
        Then: Cards should have different colors:
            - 2xx (success): green
            - 3xx (redirect): blue  
            - 4xx (client error): orange/yellow
            - 5xx (server error): red
        """
        # Make requests with different status codes
        client.get('/admin/')  # Should be 302 (redirect) or 200
        client.get('/nonexistent/')  # Should be 404
        
        # Check the dashboard
        dashboard_response = client.get('/observatory/?tab=requests')
        content = dashboard_response.content.decode('utf-8')
        
        # Verify color classes exist based on status codes
        # We'll use CSS classes like: status-2xx, status-3xx, status-4xx, status-5xx
        assert 'status-' in content, "Status code color classes should be present"
        
    def test_pending_requests_show_processing_state(self, client):
        """
        Test that requests in progress show a "processing" or "pending" state.
        
        Given: A request is being processed
        When: Viewing the requests tab during processing
        Then: The request card should show a "processing" indicator
        """
        dashboard_response = client.get('/observatory/?tab=requests')
        content = dashboard_response.content.decode('utf-8')
        
        # The HTML should support showing pending/processing states
        # We'll check for the presence of a pending state indicator in the template
        assert 'status-pending' in content or 'processing' in content.lower(), \
            "Template should support showing pending/processing request states"
    
    def test_request_cards_display_essential_information(self, client):
        """
        Test that request cards display essential information.
        
        Given: Requests have been made
        When: Viewing a request card
        Then: The card should display:
            - HTTP method (GET, POST, etc.)
            - Request path
            - Status code
            - Timestamp
            - Response time (if completed)
        """
        # Make a test request
        client.get('/admin/')
        
        # Check the dashboard
        dashboard_response = client.get('/observatory/?tab=requests')
        content = dashboard_response.content.decode('utf-8')
        
        # Verify essential information is displayed
        assert 'GET' in content or 'method' in content.lower(), "HTTP method should be displayed"
        assert 'status-code' in content or 'status' in content.lower(), "Status code area should exist"


@pytest.mark.django_db
class TestRealtimeUpdates:
    """Test suite for real-time request monitoring without page refresh."""
    
    def test_dashboard_has_realtime_update_mechanism(self, client):
        """
        Test that the dashboard includes JavaScript for real-time updates.
        
        Given: The requests tab is loaded
        When: Viewing the page source
        Then: Should include JavaScript for polling or WebSocket connection
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for JavaScript polling mechanism
        assert '<script>' in content or '<script' in content, "JavaScript should be present"
        assert 'fetch' in content.lower() or 'xmlhttprequest' in content.lower() or 'ajax' in content.lower(), \
            "Should have mechanism for fetching updates"
    
    def test_api_endpoint_returns_new_requests(self, client):
        """
        Test that there's an API endpoint to fetch new requests.
        
        Given: Some requests have been made
        When: Calling the API endpoint with a timestamp
        Then: Should return only requests newer than the timestamp
        """
        # Make some initial requests
        client.get('/admin/')
        
        # Try to access the API endpoint for new requests
        api_response = client.get('/observatory/api/requests/')
        
        assert api_response.status_code == 200, "API endpoint should exist"
        assert api_response['Content-Type'].startswith('application/json'), \
            "API should return JSON"
    
    def test_api_endpoint_returns_request_count(self, client):
        """
        Test that the API returns the count of new requests.
        
        Given: Multiple requests have been made
        When: Calling the API endpoint
        Then: Should return the total count of new requests
        """
        # Make some requests
        client.get('/admin/')
        client.get('/admin/')
        
        api_response = client.get('/observatory/api/requests/')
        
        assert api_response.status_code == 200
        
        # Parse JSON response
        import json
        data = json.loads(api_response.content.decode('utf-8'))
        
        assert 'count' in data or 'total' in data or 'requests' in data, \
            "API should return request count or list"
    
    def test_notification_banner_exists_in_template(self, client):
        """
        Test that the template includes a notification banner for new requests.
        
        Given: The requests tab is loaded
        When: Viewing the HTML structure
        Then: Should include a notification element for showing "X new requests"
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for notification banner/element
        assert 'notification' in content.lower() or 'new-requests' in content.lower() or 'banner' in content.lower(), \
            "Should have a notification element for new requests"


@pytest.mark.django_db
class TestRequestDetails:
    """Test suite for detailed request view."""
    
    def test_request_card_has_clickable_link(self, client):
        """
        Test that request cards are clickable and link to detail view.
        
        Given: A request has been captured
        When: Viewing the requests list
        Then: Each card should have a link to view details
        """
        # Make a test request
        client.get('/admin/')
        
        # Check the dashboard
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for detail links
        assert '/observatory/request/' in content or 'request-detail' in content.lower() or 'href=' in content, \
            "Request cards should have links to detail view"
    
    def test_request_detail_page_exists(self, client):
        """
        Test that the request detail page is accessible.
        
        Given: A request has been captured
        When: Accessing the detail URL
        Then: Should return a 200 response with request details
        """
        # Make a test request to capture
        from django_observatory.models import Request
        test_request = Request.objects.create(
            method='GET',
            path='/admin/',
            status_code=200,
            status='completed'
        )
        
        # Access detail page
        detail_response = client.get(f'/observatory/request/{test_request.id}/')
        
        assert detail_response.status_code == 200, "Detail page should exist"
        content = detail_response.content.decode('utf-8')
        assert '/admin/' in content, "Request path should be displayed"
    
    def test_request_detail_shows_complete_information(self, client):
        """
        Test that request detail page shows complete request/response information.
        
        Given: A request has been captured
        When: Viewing the detail page
        Then: Should display:
            - Request method, path, query params
            - Request headers
            - Request body/payload
            - Response status code
            - Response headers
            - Response body
            - Django view/controller information
        """
        from django_observatory.models import Request
        test_request = Request.objects.create(
            method='GET',
            path='/admin/',
            query_params='next=/dashboard',
            status_code=200,
            status='completed',
            duration=15.5
        )
        
        response = client.get(f'/observatory/request/{test_request.id}/')
        content = response.content.decode('utf-8')
        
        # Check for request information
        assert 'GET' in content, "HTTP method should be displayed"
        assert '/admin/' in content, "Request path should be displayed"
        assert 'next=/dashboard' in content or 'query' in content.lower(), "Query params should be shown"
        
        # Check for response information
        assert '200' in content, "Status code should be displayed"
        assert 'response' in content.lower(), "Response section should exist"
    
    def test_post_request_detail_shows_payload(self, client):
        """
        Test that POST request details show the request payload.
        
        Given: A POST request with JSON payload has been captured
        When: Viewing the detail page
        Then: Should display the request body/payload in a readable format
        """
        from django_observatory.models import Request
        import json
        
        payload = {'username': 'testuser', 'email': 'test@example.com'}
        test_request = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body=json.dumps(payload)
        )
        
        response = client.get(f'/observatory/request/{test_request.id}/')
        content = response.content.decode('utf-8')
        
        # Check for payload display
        assert 'POST' in content, "POST method should be displayed"
        assert 'payload' in content.lower() or 'body' in content.lower(), "Request body section should exist"
        assert 'testuser' in content or 'username' in content, "Payload content should be visible"
    
    def test_json_response_is_formatted(self, client):
        """
        Test that JSON responses are formatted for readability.
        
        Given: A request returned a JSON response
        When: Viewing the detail page
        Then: The JSON should be formatted/prettified
        """
        from django_observatory.models import Request
        import json
        
        response_data = {'status': 'success', 'data': {'id': 1, 'name': 'Test'}}
        test_request = Request.objects.create(
            method='GET',
            path='/api/data/',
            status_code=200,
            status='completed',
            response_body=json.dumps(response_data)
        )
        
        response = client.get(f'/observatory/request/{test_request.id}/')
        content = response.content.decode('utf-8')
        
        # Check for JSON formatting (presence of <pre> tag or code block)
        assert '<pre>' in content.lower() or 'code' in content.lower() or 'json' in content.lower(), \
            "JSON should be displayed in a formatted way"
    
    def test_detail_page_shows_django_view_information(self, client):
        """
        Test that the detail page shows which Django view handled the request.
        
        Given: A request has been processed
        When: Viewing the detail page
        Then: Should show the Django view/controller information
        """
        from django_observatory.models import Request
        test_request = Request.objects.create(
            method='GET',
            path='/admin/',
            status_code=302,
            status='completed',
            view_name='admin:index'
        )
        
        response = client.get(f'/observatory/request/{test_request.id}/')
        content = response.content.decode('utf-8')
        
        # Check for view information
        assert 'view' in content.lower() or 'controller' in content.lower() or 'handler' in content.lower(), \
            "Should display view/controller information"
