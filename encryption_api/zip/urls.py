from django.urls import path
from . import views

urlpatterns = [
    path('zip', views.zip, name='zip'),
    path('zip/<path:req_id>', views.check_status, name='check_status'),
    ]
