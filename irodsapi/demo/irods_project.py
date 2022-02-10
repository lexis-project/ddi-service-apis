import pdb

import json

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .utils import randomString, GetUserAndTokenWeb, GetUserAndTokenAPI, AuthURL, MalformedRequest, S201, E403

from django.http import HttpResponse

from .settings import IRODS

from irods.session import iRODSSession
from irods.manager.collection_manager import CollectionManager
from irods.exception import ( CollectionDoesNotExist, CAT_NO_ACCESS_PERMISSION, CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME, SYS_NO_API_PRIV,
            UserDoesNotExist, USER_FILE_DOES_NOT_EXIST, CAT_INVALID_USER, UserGroupDoesNotExist, CAT_SUCCESS_BUT_WITH_NO_INFO,
            CAT_INVALID_ARGUMENT, USER_INVALID_USERNAME_FORMAT)
from irods.models import DataObject, DataObjectMeta, Collection, CollectionMeta

from irods.connection import ExceptionOpenIDAuthUrl

from irodsApisForWp8 import projects, user


def _createProjectIrods (request, token, authuser, projectname):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          #pdb.set_trace()
          projects.create_project (session, IRODS['zone'], projectname)
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_NO_ACCESS_PERMISSION:
          return HttpResponse ('{"errorString": "User not allowed to perform action"}', 
                  content_type='application/json', status=403)
        except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
          return HttpResponse ('{"errorString": "Project already exists"}',
                  content_type='application/json', status=409)
        except USER_INVALID_USERNAME_FORMAT:
          return MalformedRequest("Invalid project name")

    return S201() 

def _deleteProjectIrods(request, token, authuser, projectname):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          projects.remove_project (session, IRODS['zone'], projectname)
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except USER_FILE_DOES_NOT_EXIST:
          return HttpResponse (status=204)
    return HttpResponse (status=204)

@csrf_exempt
def projectIrodsAPI(request):
    (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        projectname=q['projectname']
      except:
        return MalformedRequest()
      return _createProjectIrods(request, dditoken, user, projectname)
    elif request.method=='DELETE':
      try:
        q=json.loads(request.body.decode('utf-8'))
        projectname=q['projectname']
      except:
        return MalformedRequest()
      return _deleteProjectIrods(request, dditoken, user, projectname)
    else:
      return E405()


@login_required
def projectIrodsWeb(request):
#    (token, user) = GetUserAndTokenWeb(request)
#    return _createUserIrods(request, token, user)
    return HttpResponse ('{"status": "501", "errorString": "Not Implemented, please use JSON API"}',           
              content_type='application/json', status=501)



@csrf_exempt
def projectIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return projectIrodsAPI(request)
    else:
      return projectIrodsWeb(request)

def _ProjectUserIrods (request, token, authuser, username, projectname):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          #pdb.set_trace()
          user.add_user_to_project (session, projectname, username, IRODS['zone'], IRODS['federated'])
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_INVALID_USER:
            return HttpResponse ('{"status": "409", "errorString": "User does not exist"}',
                    content_type='application/json', status=409)
        except UserGroupDoesNotExist:
            return HttpResponse ('{"status": "409", "errorString": "Project does not exist"}',
                    content_type='application/json', status=409)
        except SYS_NO_API_PRIV:
            return E403()
        except CAT_NO_ACCESS_PERMISSION:
          return HttpResponse ('{"status": "403", "errorString": "User not allowed to perform action"}',
                  content_type='application/json', status=403)
        except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
          return HttpResponse ('{"status": "409", "errorString": "User already belongs to Project"}',
                  content_type='application/json', status=409)
    return S201()

def _deleteProjectUserIrods(request, token, authuser, username, projectname):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          user.remove_user_from_project (session, projectname, username, IRODS['zone'], IRODS['federated'])
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_INVALID_USER:
          return HttpResponse ('{"status": "409", "errorString": "User does not exist"}',
                    content_type='application/json', status=409)
        except CAT_SUCCESS_BUT_WITH_NO_INFO:
          return HttpResponse (status=204)
        except UserGroupDoesNotExist:
          return HttpResponse (status=204)
        except SYS_NO_API_PRIV:
            return E403()
#        except USER_FILE_DOES_NOT_EXIST:
#          return HttpResponse ('{"status": "204", "errorString": "Project does not exist"}',
#                  content_type='application/json', status=204)
    return HttpResponse (status=204)

@csrf_exempt
def projectUserIrodsAPI(request):
    (dditoken, user, refreshtoken, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        projectname=q['projectname']
        username=q['username']
      except:
        return MalformedRequest()
      return _ProjectUserIrods(request, dditoken, user, username, projectname)
    elif request.method=='DELETE':
      try:
        q=json.loads(request.body.decode('utf-8'))
        projectname=q['projectname']
        username=q['username']
      except:
        return MalformedRequest()
      return _deleteProjectUserIrods(request, dditoken, user, username, projectname)
    else:
      return E405()


@login_required
def projectUserIrodsWeb(request):
#    (token, user) = GetUserAndTokenWeb(request)
#    return _createUserIrods(request, token, user)
    return HttpResponse ('{"status": "501", "errorString": "Not Implemented, please use JSON API"}',
              content_type='application/json', status=501)


@csrf_exempt
def projectUserIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return projectUserIrodsAPI(request)
    else:
      return projectUserIrodsWeb(request)

###
def _ProjectAdminIrods (request, token, authuser, username, projectname):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          #pdb.set_trace()
          user.add_admin_user_to_project (session, projectname, username, IRODS['zone'], IRODS['federated'])
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_INVALID_ARGUMENT:
          return HttpResponse ('{"status": "409", "errorString": "User does not belong to project""}',
                  content_type='application/json', status=409)
        except CAT_INVALID_USER:
            return HttpResponse ('{"status": "409", "errorString": "User does not exist"}',
                    content_type='application/json', status=409)
        except UserGroupDoesNotExist:
            return HttpResponse ('{"status": "409", "errorString": "Project does not exist"}',
                    content_type='application/json', status=409)
        except SYS_NO_API_PRIV:
            return E403()
#        except CAT_NO_ACCESS_PERMISSION:
#          return HttpResponse ('{"status": "403", "errorString": "User not allowed to perform action"}',
#                  content_type='application/json', status=403)
        except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
          return HttpResponse ('{"status": "409", "errorString": "User is already admin of Project"}',
                  content_type='application/json', status=409)
        except CAT_NO_ACCESS_PERMISSION: 
          return HttpResponse ('{"status": "502", "errorString": "Irods misconfiguration, no access permission"}', 
                  content_type='application/json', status=502)
    return S201()


def _deleteProjectAdminIrods(request, token, authuser, username, projectname):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=authuser,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          user.revoke_admin_status_to_user (session, projectname, username, IRODS['federated'])
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_INVALID_USER:
            return HttpResponse ('{"status": "409", "errorString": "User does not exist"}',
                    content_type='application/json', status=409)
        except CAT_SUCCESS_BUT_WITH_NO_INFO:
          return HttpResponse (status=204)
        except UserGroupDoesNotExist:
          return HttpResponse (status=204)
        except SYS_NO_API_PRIV:
          return E403()

#        except USER_FILE_DOES_NOT_EXIST:
#          return HttpResponse ('{"status": "204", "errorString": "Project does not exist"}',
#                  content_type='application/json', status=204)
    return HttpResponse (status=204)


@csrf_exempt
def projectAdminIrodsAPI(request):
    (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        projectname=q['projectname']
        username=q['username']
      except:
        return MalformedRequest()
      return _ProjectAdminIrods(request, dditoken, user, username, projectname)
    elif request.method=='DELETE':
      try:
        q=json.loads(request.body.decode('utf-8'))
        projectname=q['projectname']
        username=q['username']
      except:
        return MalformedRequest()
      return _deleteProjectAdminIrods(request, dditoken, user, username, projectname)
    else:
      return E405()


@login_required
def projectAdminIrodsWeb(request):
#    (token, user) = GetUserAndTokenWeb(request)
#    return _createUserIrods(request, token, user)
    return HttpResponse ('{"status": "501", "errorString": "Not Implemented, please use JSON API"}',
              content_type='application/json', status=501)

@csrf_exempt
def projectAdminIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return projectAdminIrodsAPI(request)
    else:
      return projectAdminIrodsWeb(request)

