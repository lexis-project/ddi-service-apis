from django.http import ( FileResponse, HttpResponse )
from django.views.decorators.csrf import csrf_exempt

import json
from .utils import (GetUserAndTokenAPI, MalformedRequest, E501)
from .settings import STAGING

import pdb

@csrf_exempt
def download (request):
    #pdb.set_trace()
    (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
    if err is not None:
       return err
    if request.method != 'POST':
       return E501()
    try:
       q=json.loads(request.body.decode('utf-8'))
       source = q["source_system"]
       path = q["source_path"]
       if source != STAGING["target_system"]:
          return MalformedRequest("Invalid source_system")
       if path.find("/../") != -1:
          return MalformedRequest("Invalid source_path")
       return FileResponse(open(STAGING["path"]+"/"+path, 'rb'))
    except json.decoder.JSONDecodeError:
       return MalformedRequest("Invalid JSON")
    except KeyError:
       return MalformedRequest("Required field missing")
    except IsADirectoryError:
       return MalformedRequest("Invalid source_path")
    except FileNotFoundError:
        return HttpResponse ('{"errorString": "Data does not exist or insufficient permissions"}',
                                               content_type='application/json', status=403)
