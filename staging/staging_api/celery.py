from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'staging_api.settings')
app = Celery('staging_api')
#app = Celery('staging_api', broker=settings.BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
