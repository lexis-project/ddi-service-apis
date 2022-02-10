from django.urls import path
from . import views
from django_tus.views import TusUpload

urlpatterns = [
    path(
        'download',
        views.stage_download,
        name='download'),
    path(
        'download/<uuid:request_id>',
        views.download_staged,
        name='download'),
    path(
        'status',
        views.list_transfers,
        name='list_transfers'
    ),
    path(
        'status/<path:req_id>',
        views.get_transfer,
        name='transfer_status'
    ),
    path('upload/', # Keep the slash '/' here, otherwise Location header will be messed up
         views.tus_upload,
         name='tus_upload'
    ),
    path('upload/<uuid:resource_id>',
         TusUpload.as_view(),
         name='tus_upload_chunks'
    )
]