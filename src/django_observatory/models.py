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
    
    # Response information
    status_code = models.IntegerField(null=True, blank=True)
    
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
