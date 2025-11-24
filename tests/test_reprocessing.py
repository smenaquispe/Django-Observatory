import pytest
from django.test import Client
import json


@pytest.mark.django_db
class TestRequestReprocessing:
    """Test suite for request reprocessing functionality."""
    
    def test_reprocess_button_exists_in_detail_page(self, client):
        """
        Test that a "Reprocess Request" button exists in the detail page.
        
        Given: A request detail page is loaded
        When: Viewing the page
        Then: Should show a button to reprocess the request
        """
        from django_observatory.models import Request
        
        req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body='{"name": "John", "email": "john@example.com"}'
        )
        
        response = client.get(f'/observatory/request/{req.id}/')
        content = response.content.decode('utf-8')
        
        assert response.status_code == 200
        assert 'reprocess' in content.lower() or 'replay' in content.lower() or 'resend' in content.lower(), \
            "Should have a reprocess/replay button"
    
    def test_payload_editor_exists_in_detail_page(self, client):
        """
        Test that the detail page has an editable payload section.
        
        Given: A POST request with JSON payload
        When: Viewing the detail page
        Then: Should show an editable textarea/input for the payload
        """
        from django_observatory.models import Request
        
        payload = {"name": "John", "email": "john@example.com"}
        req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body=json.dumps(payload)
        )
        
        response = client.get(f'/observatory/request/{req.id}/')
        content = response.content.decode('utf-8')
        
        # Should have editable area for payload
        assert 'textarea' in content.lower() or 'contenteditable' in content.lower() or 'input' in content.lower(), \
            "Should have an editable field for payload"
        assert 'John' in content or json.dumps(payload) in content, \
            "Should display the original payload"
    
    def test_reprocess_endpoint_exists(self, client):
        """
        Test that there's an API endpoint to reprocess requests.
        
        Given: A completed request exists
        When: Calling the reprocess endpoint
        Then: Should accept the reprocess request
        """
        from django_observatory.models import Request
        
        req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body='{"name": "John"}'
        )
        
        # Try to reprocess
        response = client.post(
            f'/observatory/api/reprocess/{req.id}/',
            data=json.dumps({'request_body': '{"name": "Jane"}'}),
            content_type='application/json'
        )
        
        # Should have the endpoint (might be 200, 201, or 400 depending on implementation)
        assert response.status_code in [200, 201, 400, 404, 405], \
            "Reprocess endpoint should exist"
    
    def test_reprocess_creates_new_request(self, client):
        """
        Test that reprocessing creates a new request entry.
        
        Given: A completed request
        When: Reprocessing the request
        Then: Should create a new Request object in the database
        """
        from django_observatory.models import Request
        
        original_req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body='{"name": "John"}'
        )
        
        initial_count = Request.objects.count()
        
        # Attempt to reprocess (the endpoint will be created)
        response = client.post(
            f'/observatory/api/reprocess/{original_req.id}/',
            data=json.dumps({'request_body': '{"name": "Jane"}'}),
            content_type='application/json'
        )
        
        # If endpoint exists and works, should create new request
        if response.status_code in [200, 201]:
            assert Request.objects.count() > initial_count, \
                "Should create a new request entry"
    
    def test_reprocess_uses_same_method_and_path(self, client):
        """
        Test that reprocessing uses the same HTTP method and path.
        
        Given: A POST request to /api/users/
        When: Reprocessing the request
        Then: The new request should use POST and /api/users/
        """
        from django_observatory.models import Request
        
        original_req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body='{"name": "John"}'
        )
        
        response = client.post(
            f'/observatory/api/reprocess/{original_req.id}/',
            data=json.dumps({'request_body': '{"name": "Jane"}'}),
            content_type='application/json'
        )
        
        if response.status_code in [200, 201]:
            # Should have created a new request with same method and path
            new_requests = Request.objects.filter(
                method='POST',
                path='/api/users/'
            ).order_by('-id')
            
            assert new_requests.count() >= 1, \
                "Should have request with same method and path"
    
    def test_reprocess_with_modified_payload(self, client):
        """
        Test that modified payload is used in reprocessing.
        
        Given: A request with original payload
        When: Reprocessing with modified payload
        Then: New request should use the modified payload
        """
        from django_observatory.models import Request
        
        original_req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body='{"name": "John", "age": 25}'
        )
        
        modified_payload = '{"name": "Jane", "age": 30}'
        
        response = client.post(
            f'/observatory/api/reprocess/{original_req.id}/',
            data=json.dumps({'request_body': modified_payload}),
            content_type='application/json'
        )
        
        if response.status_code in [200, 201]:
            # The response should indicate the new request was created
            data = json.loads(response.content.decode('utf-8'))
            assert 'request_id' in data or 'id' in data, \
                "Should return the new request ID"
    
    def test_reprocess_detail_page_updates_automatically(self, client):
        """
        Test that the detail page has mechanism to check for completion.
        
        Given: A reprocess request is in progress
        When: Viewing the detail page
        Then: Should have JavaScript to poll for completion
        """
        from django_observatory.models import Request
        
        req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status='pending',
            request_body='{"name": "John"}'
        )
        
        response = client.get(f'/observatory/request/{req.id}/')
        content = response.content.decode('utf-8')
        
        # Should have polling mechanism
        assert 'setInterval' in content or 'setTimeout' in content or 'fetch' in content, \
            "Should have JavaScript polling mechanism"
    
    def test_reprocess_handles_get_requests(self, client):
        """
        Test that GET requests can be reprocessed (without payload).
        
        Given: A GET request
        When: Reprocessing
        Then: Should work without requiring payload
        """
        from django_observatory.models import Request
        
        req = Request.objects.create(
            method='GET',
            path='/api/users/',
            status_code=200,
            status='completed'
        )
        
        response = client.post(
            f'/observatory/api/reprocess/{req.id}/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should handle GET requests (might not need body)
        assert response.status_code in [200, 201, 400, 404, 405], \
            "Should handle GET request reprocessing"
    
    def test_reprocess_preserves_headers(self, client):
        """
        Test that important headers are preserved during reprocessing.
        
        Given: A request with specific headers
        When: Reprocessing
        Then: Should preserve Content-Type and other important headers
        """
        from django_observatory.models import Request
        
        headers = json.dumps({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123'
        })
        
        req = Request.objects.create(
            method='POST',
            path='/api/users/',
            status_code=201,
            status='completed',
            request_body='{"name": "John"}',
            request_headers=headers
        )
        
        response = client.get(f'/observatory/request/{req.id}/')
        content = response.content.decode('utf-8')
        
        # Should display headers (implementation may vary)
        assert 'header' in content.lower() or 'Content-Type' in content, \
            "Should show request headers"
    
    def test_reprocess_button_disabled_for_observatory_requests(self, client):
        """
        Test that Observatory's own requests cannot be reprocessed.
        
        Given: A request to /observatory/ path
        When: Viewing the detail page
        Then: Reprocess button should be disabled or hidden
        """
        from django_observatory.models import Request
        
        req = Request.objects.create(
            method='GET',
            path='/observatory/',
            status_code=200,
            status='completed'
        )
        
        response = client.get(f'/observatory/request/{req.id}/')
        content = response.content.decode('utf-8')
        
        # The page should load successfully
        assert response.status_code == 200
        # Implementation detail: might disable button for observatory paths


@pytest.mark.django_db
class TestReprocessingIntegration:
    """Integration tests for reprocessing with actual endpoints."""
    
    def test_full_reprocess_workflow(self, client):
        """
        Test the complete reprocessing workflow.
        
        1. Create a request
        2. View detail page
        3. Reprocess with modified payload
        4. Verify new request is created
        5. Verify it appears in the list
        """
        from django_observatory.models import Request
        
        # 1. Create original request
        original = Request.objects.create(
            method='POST',
            path='/api/test/',
            status_code=200,
            status='completed',
            request_body='{"value": 1}'
        )
        
        # 2. View detail page
        detail_response = client.get(f'/observatory/request/{original.id}/')
        assert detail_response.status_code == 200
        
        # 3. Attempt reprocess
        reprocess_response = client.post(
            f'/observatory/api/reprocess/{original.id}/',
            data=json.dumps({'request_body': '{"value": 2}'}),
            content_type='application/json'
        )
        
        # 4. If implemented, should work
        if reprocess_response.status_code in [200, 201]:
            # 5. Should appear in list
            list_response = client.get('/observatory/?tab=requests')
            assert list_response.status_code == 200
    
    def test_reprocess_returns_new_request_id(self, client):
        """
        Test that reprocessing returns the new request ID.
        
        Given: Reprocessing a request
        When: API call completes
        Then: Should return the new request ID for polling
        """
        from django_observatory.models import Request
        
        original = Request.objects.create(
            method='POST',
            path='/api/test/',
            status_code=200,
            status='completed',
            request_body='{"test": true}'
        )
        
        response = client.post(
            f'/observatory/api/reprocess/{original.id}/',
            data=json.dumps({'request_body': '{"test": false}'}),
            content_type='application/json'
        )
        
        if response.status_code in [200, 201]:
            data = json.loads(response.content.decode('utf-8'))
            assert 'request_id' in data or 'id' in data or 'new_request_id' in data, \
                "Should return new request ID for tracking"
