import pdb
import logging
import urllib.parse
import os.path
import jwt

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve
from django.http import FileResponse

from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .settings import GLOBUS

import urllib.parse

from .utils import (GetUserAndTokenAPI,  requestValidateToken, E403, E405, E501Web, E501, 
   introspect, exchangetoken, userinfo, getDDIAttributes, getPassword, getListableProjects)

logger = logging.getLogger('django')

# Create your views here.

@login_required
def getToken(request):
    #pdb.set_trace()
    t=request.session.get('oidc_access_token', None)
    if t is None:
        return render(request, 'demo/getToken.html', {'token':"Token not provided", 'decoded':None, 'introspect':None})
    d=jwt.decode (t, verify=False)
    i=introspect(t)
    if i["active"] != True:
       return render(request, 'demo/getToken.html', {'token':t, 'decoded':d, 'introspect':i})

    e=exchangetoken(t) 
    dditoken=e["access_token"]
    refreshtoken=e["refresh_token"]
    u=userinfo(dditoken)
#    a=getDDIAttributes(dditoken)
#    p=getPassword ("wp5", a)
#    l=getListableProjects(a)
    return render(request, 'demo/getToken.html', {'token':t, 'decoded':d, 'introspect':i, 'exchanged':e, 'userinfo':u})

@login_required
def validateToken(request):
    #pdb.set_trace()
    req = requestValidateToken (request.session.get('oidc_access_token', None))
    if req.status_code == 200:
       return render(request, 'demo/validateToken.html', {'response': req.status_code, 'json': req.json()})
    else:
       return render(request, 'demo/validateToken.html', {'response': req.status_code, 'json': "{}"}, status=req.status_code)


def index(request):
    return render(request, 'demo/index.html')


def _cert(request):
  filepath = GLOBUS["cert"]
  return serve(request, os.path.basename(filepath), os.path.dirname(filepath))

@csrf_exempt
def certAPI(request):
  (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
  if resp is not None:
     return resp
  return _cert(request)

@login_required
def certWeb(request):
  return _cert(request)

def cert(request):
  if request.content_type=='application/json' or request.content_type=='text/json':
    return certAPI(request)
  else:
    return certWeb(request)

def provider_logout(request):
    # See your provider's documentation for details on if and how this is
    # supported
    #https://stackoverflow.com/questions/37108782/keycloak-logout-request
    back_url=request.build_absolute_uri('/')
    encoded=urllib.parse.quote(back_url)
    redirect_url = settings.KEYCLOAK_LOGOUT_ENDPOINT + '?redirect_uri='+encoded
    return redirect_url
