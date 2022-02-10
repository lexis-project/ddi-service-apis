import pdb
import logging
import urllib.parse
import os
import json
import subprocess
import re
import shutil

from sshpubkeys import SSHKey
import sshpubkeys

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve
from django.http import FileResponse

from django.views.decorators.csrf import csrf_exempt, csrf_protect

import urllib.parse

from .utils import (GetUserAndTokenAPI,  requestValidateToken, MalformedRequest, E403, E405, E501Web, E501, randomString)
from .settings import SSHFS

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
def sshfsexport(request):
    #pdb.set_trace()
    (token, user, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        pubkey=q['pubkey']
        try:
            ssh=SSHKey(pubkey, strict=True)
            ssh.parse()
        except sshpubkeys.exceptions.InvalidKeyError as err:
            return MalformedRequest("Invalid public key: "+str(err))
        except sshpubkeys.exceptions.NotImplementedError as err:
            return MalformedRequest("Invalid public key: "+str(err))
        except sshpubkeys.exceptions.MalformedDataError as err:
            return MalformedRequest("Invalid public key: "+str(err))
        except:
            return MalformedRequest("Invalid public key")
        path=q['path']
        host=q['host']
        #assert path has no strange elements to avoid escaping chroot
        to_find = re.compile("[^a-z_0-9-]")
        match_obj = to_find.search(path)
        if match_obj is not None:
            return HttpResponse('{"errorString": "Incorrect path: single directory name required"}',  content_type='application/json', status=403)

      except:
        return MalformedRequest()
      user=randomString(SSHFS["userlen"])

      try:
        finalpath=SSHFS["path"]+"/"+path
        proc = subprocess.run(['sudo','/usr/sbin/useradd','-G', SSHFS["group"], '-s', '/usr/sbin/nologin', '-d', finalpath, user], env={'UMASK': '0000'})
        if proc.returncode != 0:
            return HttpResponse('{"errorString": "Unable to create user"}',  content_type='application/json', status=503)

        # Write the public key to the keyfile
        with open(os.path.join(SSHFS['keydir'],user),'w') as keyfile:
            keyfile.write("from=\"{0}\" {1}".format(host, pubkey))
      except Exception as e:
        return HttpResponse('{"errorString": "Unable to setup account."}', content_type='application/json', status=503)

      sshfs=user+"@"+SSHFS["host"]+":"
      return HttpResponse ('{"user": "%s", "sshfs": "%s"}'%(user, sshfs), content_type='application/json', status=201)
    elif request.method=='DELETE':
        try:
          q=json.loads(request.body.decode('utf-8'))
          user=q['user']
          path=q['path']
        except:
          return MalformedRequest("Required parameter not provided")
        try:
# ensure user is exactly 10 chars to avoid attack on other users
          to_find = re.compile("[^a-z0-9]")
          match_obj = to_find.search(user)
          if match_obj is not None or len(user) != 10:
            return HttpResponse('{"errorString": "Incorrect user"}',  content_type='application/json', status=403)
          to_find = re.compile("[^a-z_0-9-]")
          match_obj = to_find.search(path)
          if match_obj is not None or len(path) < 1:
              return HttpResponse('{"errorString": "Incorrect path: single directory name required"}',  content_type='application/json', status=403)
#cleanup
          # Delete the keyfile, fail silently
          try:
            os.remove(os.path.join(SSHFS['keydir'],user))
          except OSError as e:
              logger.error("User {0} keyfile does not exist.".format(user))

          proc = subprocess.run(['sudo','/usr/sbin/userdel', user])
          if proc.returncode != 0:
            return HttpResponse('{"errorString": "Unable to delete user"}',  content_type='application/json', status=403)

        except FileNotFoundError:
          return HttpResponse('{"errorString": "ssh export not found"}', content_type='application/json', status=404)
        except:
          return HttpResponse('{"errorString": "Unable to remove user"}', content_type='application/json', status=404)
        return HttpResponse (content_type='application/json', status=204)


    else:
      return E405()