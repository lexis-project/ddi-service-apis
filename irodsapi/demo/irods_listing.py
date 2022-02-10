import json
import struct

from irods.manager.collection_manager import CollectionManager
from irods.exception import CollectionDoesNotExist
from irods.connection import ExceptionOpenIDAuthUrl
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .utils import GetUserAndTokenAPI, getIrodsPath, MalformedRequest, E403, E405, E401, E404, GetSession, getReadableProjects,AuthURL
from .settings import IRODS

def traverse(coll, recursive):
        g=[]
        i=[]
        current={}
        current["name"]=coll.name
        current["type"]="directory"
        for obj in coll.data_objects:
            o={}
            o["name"]=obj.name
            o["checksum"]=obj.checksum
            o["type"]="file"
            o["size"]=obj.size
            o["create_time"]=obj.create_time.isoformat()
            i.append(o)
        if recursive:
          for dire in coll.subcollections:
                res=traverse(dire, True)
                i.append(res)
        else:
          for dire in coll.subcollections:
              d={}
              d["name"]=dire.name
              d["type"]="directory"
              d["create_time"]=dire.create_time.isoformat()
              i.append(d)
        current["contents"]=i
        g.append(current)
        return current

@csrf_exempt
def ListDatasetAPI(request):
    (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
    if err is not None:
        return err
    readableprojects=getReadableProjects (attr)
    if request.method!='POST':
        return E405()
    try:
        q=json.loads(request.body.decode('utf-8'))
        name=q['internalID']
        access=q['access']
        project=q['project']
        if access != 'public' and project not in readableprojects:
           return E401()
        subpath = q.get('path', "")
        recursive = q.get('recursive', True)
        zone = q.get('zone', IRODS['zone'])
        irodspath=getIrodsPath(access, user, project, zone)

        session=GetSession(dditoken, user)
        coll_manager = CollectionManager(session)
        coll=coll_manager.get(irodspath+'/'+name)
        d=traverse(coll, recursive)
        return HttpResponse (json.dumps(d, sort_keys=True, indent=4), content_type='application/json')
    except KeyError:
        return MalformedRequest()
    except json.decoder.JSONDecodeError:
        return MalformedRequest()
    except CollectionDoesNotExist:
        return E404()
    except ExceptionOpenIDAuthUrl:
        return AuthURL()
    except struct.error:
        return HttpResponse ('{"errorString": "Irods-keycloak connection failed"}', content_type='application/json', status=503)
          
