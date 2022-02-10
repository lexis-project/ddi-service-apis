from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse
from django.db import models

import hashlib
import sys

import random
import string

import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode, quote_plus

import jwt
import json

from .settings import IRODS

from moz_test.settings import (KEYCLOAK_REALM, OIDC_RP_CLIENT_ID, OIDC_RP_CLIENT_SECRET)

from irods.session import iRODSSession

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def requestValidateToken(token):
    return requests.get (IRODS['openid_microservice']+'/validate_token',
             params = {'provider': 'keycloak_openid', 'access_token': token}, verify=IRODS['sslVerification'])

def revokeToken(token):
    res=requests.post(KEYCLOAK_REALM+'/protocol/openid-connect/revoke',
            data = 'token='+ token,
            auth=HTTPBasicAuth(OIDC_RP_CLIENT_ID, OIDC_RP_CLIENT_SECRET),
            headers = {'content-type': 'application/x-www-form-urlencoded'})
    return res.status_code

def introspect(token):
    res= requests.post (KEYCLOAK_REALM+'/protocol/openid-connect/token/introspect',
             data = 'token='+ token, 
             auth=HTTPBasicAuth(OIDC_RP_CLIENT_ID, OIDC_RP_CLIENT_SECRET),
             headers = {'content-type': 'application/x-www-form-urlencoded'})
    if res.status_code != 200:
       return None
    return (res.json())

def exchangetoken(token):
    params = {"grant_type":"urn:ietf:params:oauth:grant-type:token-exchange",
              "subject_token_type":"urn:ietf:params:oauth:token-type:access_token",
              "requested_token_type":"urn:ietf:params:oauth:token-type:refresh_token",
              "subject_token": token,
              "scope":"offline_access openid" }
    body=urlencode(params, quote_via=quote_plus)
    res= requests.post (KEYCLOAK_REALM+'/protocol/openid-connect/token',
             auth=HTTPBasicAuth(OIDC_RP_CLIENT_ID, OIDC_RP_CLIENT_SECRET),
             data=body,
             headers = {'content-type': 'application/x-www-form-urlencoded'})
    if res.status_code != 200:
       return None
    return res.json()       

def userinfo(token):
    res= requests.post (KEYCLOAK_REALM+'/protocol/openid-connect/userinfo',
             data = "grant_type=urn:ietf:params:oauth:grant-type:uma-ticket&audience="+OIDC_RP_CLIENT_ID,
             headers = {'content-type': 'application/x-www-form-urlencoded',
                        'Authorization': 'Bearer '+token})
    if res.status_code != 200:
       return None
    return res.json()

def getDDIAttributes (t):
    i=introspect(t)
    if i is None:
       return (None, None, None, "Introspect failed")
    if i["active"] != True:
       return (None, None, None, "Inactive token")

    e=exchangetoken(t)
    if e is None:
       return (None, None, None, "Unable to exchange")
    dditoken=e["access_token"]
    refreshtoken=e["refresh_token"]
    u=userinfo(dditoken)
    if u is None:
       return (None, dditoken, refreshtoken, "Unable to get User Info") 
    #pdb.set_trace()
    try:
      a=u["attributes"]
    except KeyError:
      # access to public datasets allowed for everybody
      return (None, dditoken, refreshtoken, None)
    return (a, dditoken, refreshtoken, None)

def getPassword (project, attributes):
    #pdb.set_trace()
    secrets= attributes["secrets"]
    for s in secrets:
        if s["PRJ"]==project:
           passphrase = s["PASSPHRASE"]
           base64_bytes = passphrase.encode('ascii')
           message_bytes = base64.b64decode(base64_bytes)
           message = message_bytes.decode('ascii')
           return message 

    return None

def getListableProjects (attributes):
    if attributes == None:
        return []
    try:
      dat_list=attributes["dat_list"]
    except KeyError:
      return []
    projects = []
    for l in dat_list:
        projects.append(l["PRJ"])
    return projects

def getReadableProjects (attributes):
    if attributes == None:
         return []
    try:
      dat_read=attributes["dat_read"]
    except KeyError:
       return []
    projects = []
    for l in dat_read:
        projects.append(l["PRJ"])
    return projects

def getWritableProjects (attributes):
    if attributes == None:
        return []
    try:
      dat_write=attributes["dat_write"]
    except KeyError:
      return []
    projects = []
    for l in dat_write:
        projects.append(l["PRJ"])
    return projects

@login_required
def GetUserAndTokenWeb(request):
    token=request.session.get('oidc_access_token', None)
    user=request.user.irods_name
    return (token, user)


@csrf_exempt
def DecodeToken(request):
    """Retrieve token from a request, and use it to obtain a DDI token and a refresh token. Extract attributes from DDI token.
    
    Keyword arguments:
    request: The request provided by django.

    Return value:
    A list with the following items:
    - dditoken
    - user
    - refresh token
    - original token
    - attributes
    - Http response with error, or None if successful.
    """
    #pdb.set_trace()
    try:
      token=request.headers.get('Authorization').split(" ")[1]
      sys.stdout.write ("Received token "+token)
      hasher = hashlib.sha256()
      hasher.update(token.encode('utf-8'))
      sys.stdout.write ("Hash of token: "+hasher.hexdigest())
    except:
      return (None, None, None, None, None, HttpResponse ('{"errorString": "Invalid Authorization"}', 
              content_type='application/json', status=401))

    (attr, dditoken, refreshtoken, err) = getDDIAttributes(token)
    if err!=None:
       return (dditoken, None, refreshtoken, token, attr, HttpResponse ('{"errorString": "%s"}'%err,
               content_type='application/json', status=401))

    req = requestValidateToken (dditoken)
    if req.status_code == 200:
       j=req.json()
       if j['active']==False:
         return (dditoken, None,  refreshtoken, token, attr, HttpResponse ('{"errorString": "Inactive DDI Token"}', 
                 content_type='application/json', status=401))
       else:
         dec=jwt.decode (dditoken, verify=False)
         user=dec.get('irods_name', dec.get('preferred_username'))
         return (dditoken, user, refreshtoken, token, attr, None)
    else:
       return (dditoken, None, refreshtoken, token, attr, HttpResponse ('{"errorString": "Error connecting to token validator service for dditoken %s (%d, %s)"}'%(
                     IRODS['openid_microservice'], req.status_code, json.dumps(str(req.content, 'utf8'))), content_type='application/json', status=503))

@csrf_exempt
def GetUserAndTokenAPI(request):
    return DecodeToken(request)

def projectHash(project):
    return 'proj'+hashlib.md5(project.encode()).hexdigest()

def AuthURL():
    return HttpResponse ('{"errorString": "Token not accepted by irods: token not valid or not validated by broker. Or user unknown to iRODS (Auth URL sent by irods)"}', content_type='application/json', status=401)

def E403():
    return HttpResponse ('{"errorString": "User not authorized to perform action"}', 
            content_type='application/json', status=403)

def E404():
    return HttpResponse ('{"errorString": "Not found"}',
            content_type='application/json', status=404)

def E405():
    return HttpResponse ('{"errorString": "Method Not Allowed"}', content_type='application/json', status=405)

def E401():
    return HttpResponse ('{"errorString": "Unauthorized."}', content_type='application/json', status=401)

def E501Web():
    return HttpResponse ('{"errorString": "Not Implemented, please use JSON API"}',
              content_type='application/json', status=501)

def E501():
    return HttpResponse ('{"errorString": "Not Implemented"}',
              content_type='application/json', status=501)


def S201():
    return HttpResponse (status=201)

def MalformedRequest(text=""):
    return HttpResponse ('{"errorString": "Malformed request. %s"}'%text, 
            content_type='application/json', status=400)

def GetSession(token, authuser):
   return iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        )

def getIrodsPathNoZone(access, user, project):
     ph = projectHash(project)
     #public projects are pre-hashed because non-members do not know the original project name.
     if access=='public':
                 return 'public/'+ph
     elif access=='project':
                 return 'project/'+ph
     else: #user
                 return 'user/'+ph+'/'+user

def getIrodsPath(access, user, project, zone=IRODS['zone']):
             return '/'+zone+'/' + getIrodsPathNoZone(access, user, project)
