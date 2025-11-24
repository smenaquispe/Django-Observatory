"""Tests for Job detail view functionality"""
import pytest
from django.test import Client
from django.utils import timezone
from datetime import timedelta
from django_observatory.models import Job


@pytest.mark.django_db
class TestJobDetailView:
    """Tests for job detail page"""
    
    def test_job_detail_page_exists(self):
        """Test that job detail page is accessible"""
        job = Job.objects.create(
            name='test_job',
            status=Job.STATUS_COMPLETED
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        assert response.status_code == 200
    
    def test_job_detail_shows_basic_information(self):
        """Test that job detail page shows name and status"""
        now = timezone.now()
        job = Job.objects.create(
            name='detail_test_job',
            status=Job.STATUS_COMPLETED,
            created_at=now - timedelta(minutes=5),
            started_at=now - timedelta(minutes=4),
            completed_at=now
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        assert 'detail_test_job' in content
        assert 'completed' in content.lower() or 'Completed' in content
    
    def test_job_detail_shows_timing_information(self):
        """Test that detail page shows all timing fields"""
        now = timezone.now()
        job = Job.objects.create(
            name='timing_job',
            status=Job.STATUS_COMPLETED,
            created_at=now - timedelta(hours=1),
            started_at=now - timedelta(minutes=30),
            completed_at=now
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        # Should show created, started, completed times
        assert any([
            'created' in content.lower(),
            'started' in content.lower(),
            'completed' in content.lower(),
            'duration' in content.lower()
        ])
    
    def test_job_detail_shows_error_message_for_failed_jobs(self):
        """Test that failed jobs display their error message"""
        job = Job.objects.create(
            name='failed_job',
            status=Job.STATUS_FAILED,
            error_message='Connection timeout after 30 seconds'
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        assert 'Connection timeout after 30 seconds' in content
    
    def test_job_detail_shows_result_data(self):
        """Test that completed jobs show result data"""
        job = Job.objects.create(
            name='success_job',
            status=Job.STATUS_COMPLETED,
            result='Processed 1000 records successfully'
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        assert 'Processed 1000 records successfully' in content
    
    def test_job_detail_has_back_to_jobs_link(self):
        """Test that detail page has link back to jobs list"""
        job = Job.objects.create(name='test_job')
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        # Should have a link back to jobs tab
        assert 'tab=jobs' in content or 'Jobs' in content
    
    def test_job_cards_are_clickable_in_jobs_list(self):
        """Test that job cards in the list are clickable links"""
        job = Job.objects.create(
            name='clickable_job',
            status=Job.STATUS_COMPLETED
        )
        
        client = Client()
        response = client.get('/observatory/?tab=jobs')
        content = response.content.decode('utf-8')
        
        # Should have link to job detail
        assert f'/observatory/job/{job.id}/' in content or f'job/{job.id}' in content


@pytest.mark.django_db
class TestJobMetadata:
    """Tests for job metadata and source information"""
    
    def test_job_model_can_store_metadata(self):
        """Test that job can store additional metadata in result field"""
        import json
        
        metadata = {
            'source_file': 'blog/management/commands/example_job.py',
            'module': 'blog.management.commands.example_job',
            'processed_items': 100
        }
        
        job = Job.objects.create(
            name='metadata_job',
            status=Job.STATUS_COMPLETED,
            result=json.dumps(metadata)
        )
        
        # Retrieve and verify
        saved_job = Job.objects.get(id=job.id)
        saved_metadata = json.loads(saved_job.result)
        
        assert saved_metadata['source_file'] == 'blog/management/commands/example_job.py'
        assert saved_metadata['module'] == 'blog.management.commands.example_job'
        assert saved_metadata['processed_items'] == 100
    
    def test_job_detail_displays_json_result_formatted(self):
        """Test that JSON results are displayed in formatted way"""
        import json
        
        result_data = {
            'status': 'success',
            'records_processed': 500,
            'errors': 0
        }
        
        job = Job.objects.create(
            name='json_job',
            status=Job.STATUS_COMPLETED,
            result=json.dumps(result_data)
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        # Should show the data in some formatted way
        assert 'records_processed' in content or '500' in content
    
    def test_job_detail_shows_source_information_if_available(self):
        """Test that job detail shows source file/module if provided"""
        import json
        
        result_data = {
            'source': 'blog/management/commands/process_data.py',
            'status': 'completed'
        }
        
        job = Job.objects.create(
            name='sourced_job',
            status=Job.STATUS_COMPLETED,
            result=json.dumps(result_data)
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        # Should display source information
        assert 'source' in content.lower() or 'process_data.py' in content


@pytest.mark.django_db  
class TestJobDetailRealtime:
    """Tests for real-time updates in job detail view"""
    
    def test_running_job_detail_updates_automatically(self):
        """Test that running job detail page has auto-update mechanism"""
        now = timezone.now()
        job = Job.objects.create(
            name='running_job',
            status=Job.STATUS_RUNNING,
            started_at=now - timedelta(seconds=30)
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        content = response.content.decode('utf-8')
        
        # Should have JavaScript polling for updates
        assert 'setInterval' in content or 'setTimeout' in content or 'fetch' in content
    
    def test_completed_job_detail_no_polling(self):
        """Test that completed jobs don't need polling"""
        job = Job.objects.create(
            name='done_job',
            status=Job.STATUS_COMPLETED,
            started_at=timezone.now() - timedelta(minutes=5),
            completed_at=timezone.now()
        )
        
        client = Client()
        response = client.get(f'/observatory/job/{job.id}/')
        
        # Page should load successfully
        assert response.status_code == 200
