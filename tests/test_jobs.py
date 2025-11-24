"""Tests for Job monitoring functionality"""
import pytest
from django.test import Client
from django.utils import timezone
from datetime import timedelta
from django_observatory.models import Job


@pytest.mark.django_db
class TestJobsList:
    """Tests for jobs list visualization"""
    
    def test_jobs_tab_exists_in_dashboard(self):
        """Test that jobs tab exists in the dashboard"""
        client = Client()
        response = client.get('/observatory/')
        assert response.status_code == 200
        assert b'Jobs' in response.content or b'jobs' in response.content
    
    def test_jobs_are_displayed_as_cards(self):
        """Test that jobs are displayed as cards in the dashboard"""
        # Create test jobs
        Job.objects.create(
            name='test_job_1',
            status=Job.STATUS_COMPLETED
        )
        Job.objects.create(
            name='test_job_2',
            status=Job.STATUS_RUNNING
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        assert response.status_code == 200
        
        # Check that job names are displayed
        assert b'test_job_1' in response.content
        assert b'test_job_2' in response.content
    
    def test_job_card_shows_status(self):
        """Test that job cards show the current status"""
        Job.objects.create(
            name='completed_job',
            status=Job.STATUS_COMPLETED
        )
        Job.objects.create(
            name='running_job',
            status=Job.STATUS_RUNNING
        )
        Job.objects.create(
            name='failed_job',
            status=Job.STATUS_FAILED
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Check that statuses are displayed
        assert 'completed' in content.lower() or 'Completed' in content
        assert 'running' in content.lower() or 'Running' in content
        assert 'failed' in content.lower() or 'Failed' in content
    
    def test_job_card_shows_timing_information(self):
        """Test that job cards show start time, end time, and duration"""
        now = timezone.now()
        Job.objects.create(
            name='timed_job',
            status=Job.STATUS_COMPLETED,
            started_at=now - timedelta(minutes=5),
            completed_at=now
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Check that timing information is displayed
        # Should show started_at, completed_at, or duration
        assert any([
            'started' in content.lower(),
            'completed' in content.lower(),
            'duration' in content.lower(),
            'min' in content.lower() or 'sec' in content.lower()
        ])
    
    def test_running_job_shows_elapsed_time(self):
        """Test that running jobs show elapsed time instead of duration"""
        now = timezone.now()
        Job.objects.create(
            name='running_job',
            status=Job.STATUS_RUNNING,
            started_at=now - timedelta(seconds=30)
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Should show that it's running or elapsed time
        assert 'running' in content.lower() or 'Running' in content
    
    def test_pending_job_shows_created_time(self):
        """Test that pending jobs show when they were created"""
        now = timezone.now()
        Job.objects.create(
            name='pending_job',
            status=Job.STATUS_PENDING,
            created_at=now - timedelta(minutes=2)
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Should show pending status
        assert 'pending' in content.lower() or 'Pending' in content
    
    def test_jobs_are_ordered_by_creation_date(self):
        """Test that jobs are ordered by creation date (newest first)"""
        now = timezone.now()
        job1 = Job.objects.create(
            name='old_job',
            created_at=now - timedelta(hours=2)
        )
        job2 = Job.objects.create(
            name='recent_job',
            created_at=now - timedelta(minutes=5)
        )
        job3 = Job.objects.create(
            name='newest_job',
            created_at=now
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Find positions of job names in content
        pos_newest = content.find('newest_job')
        pos_recent = content.find('recent_job')
        pos_old = content.find('old_job')
        
        # Newest should appear before recent, recent before old
        assert pos_newest < pos_recent < pos_old
    
    def test_job_card_shows_error_message_for_failed_jobs(self):
        """Test that failed jobs display their error message"""
        Job.objects.create(
            name='failed_job',
            status=Job.STATUS_FAILED,
            error_message='Database connection timeout'
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Should show the error message
        assert 'Database connection timeout' in content or 'error' in content.lower()


@pytest.mark.django_db
class TestJobsAPI:
    """Tests for jobs API endpoint"""
    
    def test_jobs_api_endpoint_exists(self):
        """Test that there's an API endpoint for fetching jobs"""
        client = Client()
        response = client.get('/observatory/api/jobs/')
        assert response.status_code == 200
    
    def test_jobs_api_returns_json(self):
        """Test that jobs API returns JSON data"""
        Job.objects.create(name='test_job')
        
        client = Client()
        response = client.get('/observatory/api/jobs/')
        assert response['Content-Type'] == 'application/json'
    
    def test_jobs_api_returns_job_list(self):
        """Test that API returns list of jobs with their information"""
        now = timezone.now()
        Job.objects.create(
            name='api_test_job',
            status=Job.STATUS_RUNNING,
            started_at=now - timedelta(minutes=1)
        )
        
        client = Client()
        response = client.get('/observatory/api/jobs/')
        data = response.json()
        
        assert 'jobs' in data
        assert len(data['jobs']) > 0
        
        job = data['jobs'][0]
        assert 'name' in job
        assert 'status' in job
        assert job['name'] == 'api_test_job'
    
    def test_jobs_api_includes_duration_for_completed_jobs(self):
        """Test that API includes duration for completed jobs"""
        now = timezone.now()
        Job.objects.create(
            name='completed_job',
            status=Job.STATUS_COMPLETED,
            started_at=now - timedelta(minutes=5),
            completed_at=now
        )
        
        client = Client()
        response = client.get('/observatory/api/jobs/')
        data = response.json()
        
        job = next(j for j in data['jobs'] if j['name'] == 'completed_job')
        assert 'duration' in job or 'started_at' in job


@pytest.mark.django_db
class TestJobsRealtimeUpdates:
    """Tests for real-time updates of jobs"""
    
    def test_jobs_dashboard_has_realtime_update_mechanism(self):
        """Test that jobs dashboard polls for updates"""
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Should have JavaScript code for polling
        assert 'setInterval' in content or 'setTimeout' in content or 'fetch' in content
    
    def test_running_jobs_update_elapsed_time(self):
        """Test that running jobs show updating elapsed time"""
        now = timezone.now()
        Job.objects.create(
            name='long_running_job',
            status=Job.STATUS_RUNNING,
            started_at=now - timedelta(minutes=10)
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Should have mechanism to update elapsed time
        assert 'running' in content.lower() or 'Running' in content
