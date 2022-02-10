from django.db import models

# Create your models here.

# users/models.py
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    pass
    # add additional fields in here
    irods_name = models.CharField(max_length=300)

    REQUIRED_FIELDS = [irods_name]
    
    def __str__(self):
        return self.username


class UploadedFile(models.Model):
    pass

    method = models.CharField(max_length=100, default='tus')
    internalID = models.CharField(max_length=100, default='')
    project = models.CharField(max_length=100, default='')
    user = models.CharField(max_length=100, default='')
    filename = models.CharField(max_length=255, default='')
    filenameondisk = models.CharField(max_length=255, default='')
    tusresourceid =  models.CharField(max_length=100, default='')

    REQUIRED_FIELDS = [method, project, user, filename, filenameondisk, tusresourceid]
