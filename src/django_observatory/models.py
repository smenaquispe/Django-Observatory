"""Models for Django Observatory"""
from django.db import models
from django.utils import timezone


class Request(models.Model):
    """Model to store HTTP request information"""
    
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
    ]
    
    # Request information
    method = models.CharField(max_length=10)  # GET, POST, PUT, DELETE, etc.
    path = models.CharField(max_length=2048)
    query_params = models.TextField(blank=True, null=True)
    request_headers = models.TextField(blank=True, null=True, help_text="JSON string of request headers")
    request_body = models.TextField(blank=True, null=True, help_text="Request payload")
    
    # Response information
    status_code = models.IntegerField(null=True, blank=True)
    response_headers = models.TextField(blank=True, null=True, help_text="JSON string of response headers")
    response_body = models.TextField(blank=True, null=True, help_text="Response content")
    
    # Django view information
    view_name = models.CharField(max_length=255, blank=True, null=True, help_text="Django view name/path")
    
    # Timing
    timestamp = models.DateTimeField(default=timezone.now)
    duration = models.FloatField(null=True, blank=True, help_text="Duration in milliseconds")
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code or 'Pending'}"
    
    def get_status_category(self):
        """Return the status category for color coding"""
        if self.status_code is None:
            return 'pending'
        elif 200 <= self.status_code < 300:
            return '2xx'
        elif 300 <= self.status_code < 400:
            return '3xx'
        elif 400 <= self.status_code < 500:
            return '4xx'
        elif 500 <= self.status_code < 600:
            return '5xx'
        return 'unknown'


class Job(models.Model):
    """Model to store background job/task information"""
    
    STATUS_PENDING = 'pending'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Job information
    name = models.CharField(max_length=255, help_text="Job name/identifier")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    error_message = models.TextField(blank=True, null=True, help_text="Error message if job failed")
    result = models.TextField(blank=True, null=True, help_text="Job result/output")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    def get_duration(self):
        """Calculate job duration in seconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        elif self.started_at:
            # Job is still running
            delta = timezone.now() - self.started_at
            return delta.total_seconds()
        return None
    
    def is_running(self):
        """Check if job is currently running"""
        return self.status == self.STATUS_RUNNING
