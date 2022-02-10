from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse

import random
import string

import requests

import jwt
import json

from moz_test.settings import KEYCLOAK_REALM

from .settings import IRODS # we use irods backend for authentification purposes

import pdb

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def requestValidateToken(token):
    return requests.get (IRODS['openid_microservice']+'/validate_token',
             params = {'provider': 'keycloak_openid', 'access_token': token})

@csrf_exempt
def DecodeToken(request):
    try:
      token=request.headers.get('Authorization').split(" ")[1]
    except:
      return (None, None, HttpResponse ('{"errorString": "Invalid Authorization"}', 
              content_type='application/json', status=401))
    req = requestValidateToken (token)
    if req.status_code == 200:
       j=req.json()
       if j['active']==False:
         return (token, None, HttpResponse ('{"errorString": "Invalid Token"}', 
                 content_type='application/json', status=401))
       else:
         dec=jwt.decode (token, verify=False)
         user=dec.get('irods_name', dec.get('preferred_username'))
         return (token, user, None)
    else:
       return (None, None, HttpResponse ('{"errorString": "Error connecting to token validator service %s (%d, %s)"}'%(
                     IRODS['openid_microservice'], req.status_code, json.dumps(str(req.content, 'utf8'))), content_type='application/json', status=503))

@csrf_exempt
def GetUserAndTokenAPI(request):
    (token, user, err)=DecodeToken(request)
    if (err):
       return (None, None, err)
    return (token, user, None)

def GetProjects(token):
    dec=jwt.decode (token, verify=False)
#"/projects/X"
#           ^--10th character    
#    pdb.set_trace()
    projects=[ s[10:] for s in dec['group'] if s.startswith('/projects/') ]
    return (projects)

def E403():
    return HttpResponse ('{"errorString": "User not authorized to perform action"}', 
            content_type='application/json', status=403)

def E405():
    return HttpResponse ('{"errorString": "Method Not Allowed"}', content_type='application/json', status=405)

def E501Web():
    return HttpResponse ('{"errorString": "Not Implemented, please use JSON API"}',
              content_type='application/json', status=501)

def E501():
    return HttpResponse ('{"errorString": "Not Implemented"}',
              content_type='application/json', status=501)


def S201():
    return HttpResponse ('{"errorString": "Created"}',
              content_type='application/json', status=201)

def MalformedRequest(message=""):
    return HttpResponse ('{"errorString": "Malformed request: %s"}'%message, 
            content_type='application/json', status=400)

def checkKeycloakPermission (project, token):
#    pdb.set_trace()
    p=GetProjects(token)
    if not project in p:
         return False
    return True
