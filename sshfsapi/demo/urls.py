from django.urls import path

from . import (views)

urlpatterns = [
    path('', views.index, name='index'),
    path('sshfsexport', views.sshfsexport, name='sshfsexport'),
]

