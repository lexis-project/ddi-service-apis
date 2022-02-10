from django_tus.views import TusUpload
from django.views.decorators.csrf import csrf_exempt
from .utils import GetUserAndTokenAPI, getWritableProjects, E403, MalformedRequest
from django.dispatch import receiver
from django_tus.signals import tus_upload_finished_signal
from demo.models import UploadedFile
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def tusUpload(*args, **kwargs):
    request = args[0]
    (dditoken, user, refresh, token, attr, err) = GetUserAndTokenAPI(request)
    if err is not None:
         return err
    wp = getWritableProjects(attr)
    if len(wp) == 0:
        return E403()
    m = request.headers.get ("Upload-Metadata", None)
    if m != None:
       m = TusUpload.get_metadata (None, request)
       u = m.get ("user", None)
       if u == None:
          return MalformedRequest ("Missing tus Upload-Metadata: user")
       if user != u:
          return MalformedRequest ("Wrong value for tus Upload-Metadata: user")
       p = m.get("project", None)
       if p == None:
          return MalformedRequest ("Missing tus Upload-Metadata: project")
       if not p in wp:
          return MalformedRequest ("Wrong value for tus Upload-Metadata: project")
       f = m.get("filename", None)
       if f == None:
          return MalformedRequest ("Missing tus Upload-Metadata: filename")
    return TusUpload.as_view()(*args, **kwargs)

@receiver(tus_upload_finished_signal)
def uploadFinished(sender, **kwargs):
    # Store UploadedFile object to the DB upon successful upload
    ufp=kwargs['upload_file_path']
    resource_id = ufp.split('/')[len(ufp.split('/'))-1:][0]
    try:
      UploadedFile(filename=kwargs['metadata']['filename'], project=kwargs['metadata']['project'], 
              user=kwargs['metadata']['user'], filenameondisk=kwargs["filename"], tusresourceid=resource_id).save()
    except KeyError as e:
      print ("Required metadata is missing: "+ str(e))
      print ("metadata was: "+str(kwargs['metadata']))
