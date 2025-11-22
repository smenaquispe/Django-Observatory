import pytest
from django.test import Client


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
        # Make a GET request to the observatory endpoint
        response = client.get('/observatory/')
        
        # Assert the response is successful
        assert response.status_code == 200
        
        # Decode the response content
        content = response.content.decode('utf-8')
        
        # Assert that all three tabs are present in the response
        assert 'Requests' in content, "The 'Requests' tab should be present"
        assert 'Logs' in content, "The 'Logs' tab should be present"
        assert 'Jobs' in content, "The 'Jobs' tab should be present"
