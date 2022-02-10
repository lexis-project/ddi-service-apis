from django.db import models

class DataTransfer(models.Model):
    """
    This model is used to track ongoing transfers identified by Celery request ID.
    """
    pass

    TYPE_CHOICES = [
        ('download', 'Download transfer'),
        ('upload', 'Upload transfer')
    ]
    zone = models.CharField(max_length=100, default='')
    project = models.CharField(max_length=100, default='')
    user = models.CharField(max_length=100, default='')
    access = models.CharField(max_length=100, default='')
    filename = models.CharField(max_length=255, default='')
    request_id = models.CharField(max_length=100, default='', unique=True)
    task_id = models.CharField(max_length=100, default='', null=True)
    created_at = models.DateTimeField(auto_now=True)
    transfer_type = models.CharField(max_length=100, default='', choices=TYPE_CHOICES)

    REQUIRED_FIELDS = [zone, project, user, access, filename, transfer_type, request_id]

