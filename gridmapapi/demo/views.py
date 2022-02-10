import pdb
import logging
import urllib.parse
import os
import json
import subprocess
import re
import shutil
import requests 

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve
from django.http import FileResponse

from django.views.decorators.csrf import csrf_exempt, csrf_protect

import urllib.parse

from .utils import (IsLexisAdmin, GetUserAndTokenAPI,  requestValidateToken, MalformedRequest, E403, E405, E501Web, E501, randomString,
        getListableProjects, getReadableProjects, getWritableProjects, revokeToken)

from .settings import BACKEND

logger = logging.getLogger('django')

# Create your views here.
def index(request):
    return render(request, 'demo/index.html', {'token':request.session.get('oidc_access_token', None)})

def provider_logout(request):
    # See your provider's documentation for details on if and how this is
    # supported
    #https://stackoverflow.com/questions/37108782/keycloak-logout-request
    back_url=request.build_absolute_uri('/')
    encoded=urllib.parse.quote(back_url)
    redirect_url = settings.KEYCLOAK_LOGOUT_ENDPOINT + '?redirect_uri='+encoded
    return redirect_url

@csrf_exempt
def gridmap(request):
    (dditoken, tuser, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
   #verify user has write access to all projects 
    l = getListableProjects (attr)
    r = getReadableProjects (attr)
    w = getWritableProjects (attr)
    resp = HttpResponse('{"message": "User not authorized to use GridFTP due to current project permissions"}',
                                   content_type='application/json', status=403)
    for p in l:
        if not p in w:
            return resp
    for p in r:
        if not p in w:
            return resp

    if BACKEND is not None:
        headers = {"Authorization": "Bearer "+token}
        if request.method == "POST":
           for backend in BACKEND:
               resp=requests.post (backend, data = request.body, headers=headers, verify=False)
               if resp.status_code != 201:
                   revokeToken(dditoken)
                   return HttpResponse('{"message": "Backend responded: %s, status code: %d"}'%(json.dumps(resp.text)[1:-1], resp.status_code), 
                        content_type='application/json', status=resp.status_code)
           revokeToken(dditoken)
           return HttpResponse(status=201)
        if request.method== "DELETE":
           for backend in BACKEND:
               resp=requests.delete (backend, data=request.body, headers=headers, verify=False)
               if resp.status_code != 204:
                   revokeToken(dditoken)
                   return HttpResponse('{"message": "Backend responded: %s, status code: %d"}'%(json.dumps(resp.text)[1:-1], resp.status_code), 
                        content_type='application/json', status=resp.status_code)
           revokeToken(dditoken)
           return HttpResponse (status=204)
        return E405()
    # BACKEND None, run locally
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        dn=q['dn']
        user=q.get('user', tuser)
        if user != tuser and not IsLexisAdmin(token):
            revokeToken(dditoken)
            return HttpResponse('{"message": "User not authorized to perform task"}',  content_type='application/json', status=403)
        to_find = re.compile("[^a-z0-9]")
        match_obj = to_find.search(user)
        if match_obj is not None:
            revokeToken(dditoken)
            return HttpResponse('{"message": "Incorrect user"}',  content_type='application/json', status=403)
      except json.decoder.JSONDecodeError:
        revokeToken(dditoken)
        return MalformedRequest("Invalid json")
      except KeyError as e:
        revokeToken(dditoken)
        return MalformedRequest("Required parameter missing: "+str(e))
      try:
        proc = subprocess.run(['sudo','/usr/sbin/grid-mapfile-add-entry','-dn', dn, '-ln', user, '-force'])
        if proc.returncode != 0:
            revokeToken(dditoken)
            return HttpResponse('{"message": "Unable to add entry to gridmap"}',  content_type='application/json', status=503)
      except:
        revokeToken(dditoken)
        return HttpResponse('{"message": "Unable to add entry"}', content_type='application/json', status=503)
      revokeToken(dditoken)
      return HttpResponse (status=201)
    elif request.method=='DELETE':
        try:
          q=json.loads(request.body.decode('utf-8'))
          user=q.get('user', tuser)
        except json.decoder.JSONDecodeError:
          revokeToken(dditoken)
          return MalformedRequest("Invalid json")
        try:
          if user != tuser and not IsLexisAdmin(token):
            revokeToken(dditoken)
            return HttpResponse('{"message": "User not authorized to perform task"}',  content_type='application/json', status=403)
          to_find = re.compile("[^a-z0-9]")
          match_obj = to_find.search(user)
          if match_obj is not None:
            revokeToken(dditoken)
            return HttpResponse('{"message": "Incorrect user"}',  content_type='application/json', status=403)
          
          proc = subprocess.run(['sudo','/usr/sbin/grid-mapfile-delete-entry', '-ln', user])
          if proc.returncode != 0:
            revokeToken(dditoken)
            return HttpResponse('{"message": "Unable to delete user"}',  content_type='application/json', status=403)
          
        except:
          revokeToken(dditoken)
          return HttpResponse('{"message": "Unable to remove user"}', content_type='application/json', status=404)
        revokeToken(dditoken)
        return HttpResponse (status=204)


    else:
      revokeToken(dditoken)
      return E405()

