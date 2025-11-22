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

        response = client.get('/observatory/')
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        
        assert 'Requests' in content, "The 'Requests' tab should be present"
        assert 'Logs' in content, "The 'Logs' tab should be present"
        assert 'Jobs' in content, "The 'Jobs' tab should be present"
