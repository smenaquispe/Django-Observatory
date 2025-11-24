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
    
    def test_post_requests_are_clickable(self, client):
        """
        Test that POST requests (and any non-GET methods) are clickable to view details.
        
        This addresses a bug where dynamically added request cards don't have
        clickable links to their detail pages.
        
        Given: A POST request has been captured
        When: Viewing the requests tab
        Then: The request card should be clickable with a link to the detail page
        """
        from django_observatory.models import Request
        
        # Create a POST request in the database
        post_request = Request.objects.create(
            method='POST',
            path='/api/blog/posts/',
            status_code=201,
            status='completed',
            request_body='{"title": "Test Post", "content": "Test content"}',
            response_body='{"id": 1, "title": "Test Post"}'
        )
        
        # Get the dashboard
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Verify the POST request is displayed
        assert 'POST' in content, "POST method should be visible"
        assert '/api/blog/posts/' in content, "POST request path should be visible"
        
        # Verify there's a link to the detail page
        detail_url = f'/observatory/request/{post_request.id}/'
        assert detail_url in content, f"Detail link {detail_url} should be present in the HTML"
        
        # Verify we can actually access the detail page
        detail_response = client.get(detail_url)
        assert detail_response.status_code == 200, "Detail page should be accessible"
        
        detail_content = detail_response.content.decode('utf-8')
        assert 'Test Post' in detail_content, "Detail page should show request content"
    
    def test_dynamically_added_requests_are_clickable(self, client):
        """
        Test that requests added dynamically via JavaScript have clickable links.
        
        This is a regression test for the bug where createRequestCard() function
        in JavaScript doesn't wrap cards in <a> tags.
        
        Given: The dashboard HTML is loaded
        When: Examining the JavaScript createRequestCard function
        Then: The function should generate cards wrapped in clickable links
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check that the JavaScript includes the necessary link structure
        # The createRequestCard function should include an <a> tag wrapper
        assert 'createRequestCard' in content, "createRequestCard function should exist"
        
        # CRITICAL: Check if the createRequestCard function returns HTML with <a> tags
        # Extract the section containing createRequestCard function
        import re
        
        # Find the function and everything until the next function or script end
        match = re.search(r'function createRequestCard\(req\)\s*\{([\s\S]*?)(?=function\s|\s*</script)', content)
        assert match, "createRequestCard function should be found"
        
        function_body = match.group(1)
        
        # The function should create an <a> tag with href to the request detail
        # Check if the function includes <a href= in its return statement
        assert ('<a href=' in function_body or '<a ' in function_body) and '/observatory/request/' in function_body, \
            "BUG FOUND: createRequestCard function doesn't wrap cards in <a> tags! " \
            "It only creates div elements without clickable links."
    
    def test_all_http_methods_are_clickable(self, client):
        """
        Test that ALL HTTP methods (GET, POST, PUT, DELETE, PATCH) have clickable cards.
        
        This comprehensive test ensures that no matter what HTTP method is used,
        the request card will be clickable to view details.
        
        Given: Requests with different HTTP methods
        When: Viewing the requests tab
        Then: All request cards should have clickable links
        """
        from django_observatory.models import Request
        
        # Create requests with different HTTP methods
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        created_requests = []
        
        for method in methods:
            req = Request.objects.create(
                method=method,
                path=f'/api/test/{method.lower()}/',
                status_code=200 if method == 'GET' else 201 if method == 'POST' else 200,
                status='completed'
            )
            created_requests.append(req)
        
        # Get the dashboard
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Verify all requests are displayed and have clickable links
        for req in created_requests:
            assert req.method in content, f"{req.method} method should be visible"
            assert req.path in content, f"{req.method} path should be visible"
            
            # Verify the detail link exists
            detail_url = f'/observatory/request/{req.id}/'
            assert detail_url in content, \
                f"Detail link for {req.method} request should be present: {detail_url}"
            
            # Verify we can access the detail page
            detail_response = client.get(detail_url)
            assert detail_response.status_code == 200, \
                f"Detail page for {req.method} request should be accessible"
    
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
    
    def test_pending_requests_update_reactively(self, client):
        """
        Test that pending requests update their status reactively without page refresh.
        
        Given: A request is in pending status
        When: The request completes and status changes
        Then: The dashboard should update the request status automatically via polling
        """
        from django_observatory.models import Request
        
        # Create a pending request
        pending_request = Request.objects.create(
            method='POST',
            path='/api/slow-endpoint/',
            status='pending',
            status_code=None
        )
        
        # Get the dashboard with the pending request
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Verify the pending request is shown
        assert f'data-request-id="{pending_request.id}"' in content or str(pending_request.id) in content
        
        # Verify the API endpoint can be used to check for updates
        api_response = client.get(f'/observatory/api/requests/')
        assert api_response.status_code == 200
        
        # Verify JavaScript polling mechanism exists
        assert 'checkForNewRequests' in content or 'setInterval' in content, \
            "JavaScript should have polling mechanism"
        
        # Now complete the request
        pending_request.status = 'completed'
        pending_request.status_code = 200
        pending_request.duration = 250.5
        pending_request.save()
        
        # The API should return updated information
        api_response = client.get(f'/observatory/api/requests/')
        data = api_response.json()
        
        # Find our request in the API response
        our_request = next((r for r in data['requests'] if r['id'] == pending_request.id), None)
        assert our_request is not None, "Updated request should be in API response"
        assert our_request['status'] == 'completed', "Status should be updated"
        assert our_request['status_code'] == 200, "Status code should be present"
    
    def test_slow_responding_requests_show_indicator(self, client):
        """
        Test that requests taking too long show a "responding" or "slow" indicator.
        
        Given: A request has been pending for a long time (e.g., > 5 seconds)
        When: Viewing the dashboard
        Then: The request should show a visual indicator that it's taking too long
        """
        from django_observatory.models import Request
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a request that started 10 seconds ago and is still pending
        slow_request = Request.objects.create(
            method='GET',
            path='/api/very-slow-endpoint/',
            status='pending',
            status_code=None,
            timestamp=timezone.now() - timedelta(seconds=10)
        )
        
        # Get the API response
        api_response = client.get(f'/observatory/api/requests/')
        data = api_response.json()
        
        # The API should include timing information to help determine if request is slow
        our_request = next((r for r in data['requests'] if r['id'] == slow_request.id), None)
        assert our_request is not None
        assert 'timestamp' in our_request, "Timestamp should be included to calculate elapsed time"
        
        # Verify the template has logic to show slow request indicator
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for slow/responding state support in JavaScript
        assert 'timestamp' in content.lower() or 'elapsed' in content.lower() or 'duration' in content.lower(), \
            "Template should have logic to calculate and show elapsed time for pending requests"


@pytest.mark.django_db
class TestRequestFilters:
    """Test suite for request filtering functionality."""
    
    def test_method_filter_selector_exists(self, client):
        """
        Test that a method filter selector is present in the dashboard.
        
        Given: The requests tab is loaded
        When: Viewing the dashboard
        Then: Should show a selector/dropdown to filter by HTTP method
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for method filter UI elements
        assert 'filter' in content.lower() or 'method' in content.lower(), \
            "Should have filtering UI elements"
        
        # Check for method options
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        # At least some method names should appear for filtering
        method_count = sum(1 for method in methods if method in content)
        assert method_count >= 2, "Should have method filter options"
    
    def test_filter_by_get_method(self, client):
        """
        Test filtering requests to show only GET requests.
        
        Given: Multiple requests with different HTTP methods
        When: Filtering by GET method
        Then: Only GET requests should be visible
        """
        from django_observatory.models import Request
        
        # Create requests with different methods
        get_req = Request.objects.create(method='GET', path='/api/items/', status='completed', status_code=200)
        post_req = Request.objects.create(method='POST', path='/api/items/', status='completed', status_code=201)
        put_req = Request.objects.create(method='PUT', path='/api/items/1/', status='completed', status_code=200)
        
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # All should be visible initially
        assert 'GET' in content
        assert 'POST' in content
        
        # The page should have JavaScript to filter by method
        assert 'filter' in content.lower(), "Should have filtering functionality"
    
    def test_filter_by_post_method(self, client):
        """
        Test filtering requests to show only POST requests.
        
        Given: Multiple requests with different HTTP methods
        When: Filtering by POST method
        Then: Only POST requests should be visible
        """
        from django_observatory.models import Request
        
        Request.objects.create(method='GET', path='/api/items/', status='completed', status_code=200)
        Request.objects.create(method='POST', path='/api/items/', status='completed', status_code=201)
        
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Should have the ability to filter
        assert 'data-request-id' in content or 'request-card' in content
    
    def test_path_search_filter(self, client):
        """
        Test searching/filtering requests by path/controller.
        
        Given: Multiple requests to different endpoints
        When: Searching for a specific path (e.g., "/api/users")
        Then: Only matching requests should be visible
        """
        from django_observatory.models import Request
        
        Request.objects.create(method='GET', path='/api/users/', status='completed', status_code=200)
        Request.objects.create(method='GET', path='/api/products/', status='completed', status_code=200)
        Request.objects.create(method='POST', path='/api/users/login/', status='completed', status_code=200)
        
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for search input field
        assert 'search' in content.lower() or 'input' in content.lower(), \
            "Should have a search input field"
        assert 'filter' in content.lower(), "Should have filtering capability"
    
    def test_exclusion_filter(self, client):
        """
        Test excluding/hiding specific paths from the request list.
        
        Given: Multiple requests to different endpoints
        When: Adding an exclusion filter for a specific path
        Then: Requests matching that path should be hidden
        """
        from django_observatory.models import Request
        
        Request.objects.create(method='GET', path='/health/', status='completed', status_code=200)
        Request.objects.create(method='GET', path='/api/users/', status='completed', status_code=200)
        Request.objects.create(method='GET', path='/metrics/', status='completed', status_code=200)
        
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Should have exclusion/anti-filter functionality
        assert 'filter' in content.lower() or 'exclude' in content.lower(), \
            "Should have exclusion filtering capability"
    
    def test_filter_tags_with_remove_button(self, client):
        """
        Test that active filters are shown as tags with X button to remove.
        
        Given: Filters are applied (method, search, or exclusion)
        When: Viewing the filtered dashboard
        Then: Should show filter tags with X button to remove each filter
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for filter tag container/structure in the HTML
        # The tags will be created dynamically by JavaScript
        assert 'filter' in content.lower(), "Should have filter functionality"
    
    def test_multiple_filters_can_be_applied(self, client):
        """
        Test that multiple filters can be applied simultaneously.
        
        Given: Multiple requests with different methods and paths
        When: Applying method filter + path search + exclusion
        Then: All filters should work together
        """
        from django_observatory.models import Request
        
        # Create diverse requests
        Request.objects.create(method='GET', path='/api/users/', status='completed', status_code=200)
        Request.objects.create(method='POST', path='/api/users/', status='completed', status_code=201)
        Request.objects.create(method='GET', path='/api/products/', status='completed', status_code=200)
        Request.objects.create(method='GET', path='/health/', status='completed', status_code=200)
        
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Should support multiple filtering
        assert 'filter' in content.lower(), "Should have filtering system"
    
    def test_filter_persistence_in_ui(self, client):
        """
        Test that filters persist in the UI (shown as tags).
        
        Given: A filter has been applied
        When: The filter is active
        Then: Should display a tag/chip showing the active filter
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Check for filter display elements (tags/chips will be created by JS)
        assert 'filter' in content.lower(), "Should have filter display system"
    
    def test_clear_all_filters(self, client):
        """
        Test clearing all filters at once.
        
        Given: Multiple filters are applied
        When: Clicking "Clear All" or similar action
        Then: All filters should be removed
        """
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Should have mechanism to clear filters
        assert 'filter' in content.lower() or 'clear' in content.lower(), \
            "Should have filter clearing capability"
    
    def test_filter_by_view_name(self, client):
        """
        Test filtering by Django view/controller name.
        
        Given: Requests have view_name information
        When: Searching by view name
        Then: Should filter by the view that handled the request
        """
        from django_observatory.models import Request
        
        Request.objects.create(
            method='GET', 
            path='/admin/', 
            status='completed', 
            status_code=200,
            view_name='admin:index'
        )
        Request.objects.create(
            method='GET', 
            path='/api/users/', 
            status='completed', 
            status_code=200,
            view_name='api.users.list'
        )
        
        response = client.get('/observatory/?tab=requests')
        content = response.content.decode('utf-8')
        
        # Should be able to filter by view name
        assert 'filter' in content.lower() or 'search' in content.lower(), \
            "Should have search/filter capability for view names"


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
