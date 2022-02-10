import json

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .utils import (randomString, GetUserAndTokenWeb, GetUserAndTokenAPI, AuthURL, MalformedRequest, 
                        S201, E403, E501, E501Web, GetSession)

from django.http import HttpResponse

from .settings import IRODS

from irods.session import iRODSSession
from irods.manager.collection_manager import CollectionManager
from irods.exception import ( CollectionDoesNotExist, CAT_NO_ACCESS_PERMISSION, CAT_SUCCESS_BUT_WITH_NO_INFO, CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME, SYS_NO_API_PRIV,
            UserDoesNotExist, UserGroupDoesNotExist )
from irods.models import DataObject, DataObjectMeta, Collection, CollectionMeta

from irods.connection import ExceptionOpenIDAuthUrl

from irodsApisForWp8 import group, user

def _createUserIrods (request, token, authuser, newuser, uid):
    with GetSession(token, authuser) as session:
        try:
          user.create_user (session, newuser, 'rodsuser', IRODS['zone'], IRODS['federated'], uid)
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except SYS_NO_API_PRIV:
          return E403()
        except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
          return HttpResponse ('{"errorString": "User already exists"}',
                  content_type='application/json', status=409)


    return S201() 

def _deleteUserIrods(request, token, authuser, newuser):
    with GetSession(token, authuser) as session:
        try:
          user.delete_user (session, newuser, IRODS['federated'])
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except UserDoesNotExist:
          return HttpResponse (status=204)
        except SYS_NO_API_PRIV:
          return E403()
    return HttpResponse (status=204)

def _supportUserIrods(request, token, authuser, newuser):
  with GetSession(token, authuser) as session:
    try:
         group.add_newuser_to_lexis_sup_group(session, newuser)
         # FIXME add federated users in a loop
    except ExceptionOpenIDAuthUrl:
          return AuthURL()
    except UserGroupDoesNotExist:
          return HttpResponse ('{"errorString": "Backend misconfiguration: Support group does not exist"}',
                   content_type='application/json', status=503)
    except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
          return HttpResponse ('{"errorString": "User already in support group"}',
                  content_type='application/json', status=409)

    return S201()

def _adminUserIrods(request, token, authuser, newuser):
  with GetSession(token, authuser) as session:
    try:
         group.add_newuser_to_lexis_adm_group(session, newuser)
         # FIXME add federated users in a loop
    except ExceptionOpenIDAuthUrl:
          return AuthURL()
    except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
          return HttpResponse ('{"errorString": "User already in admin group"}',
                  content_type='application/json', status=409)

    return S201()
 

def _deleteAdminIrods(request, token, authuser, newuser):
    return E501()
#    with GetSession(token, authuser) as session:
# FIXME add federated users in a loop
#        try:
#           group.remove_user_to_lexis_adm_group(session, newuser)
#        except ExceptionOpenIDAuthUrl:
#          return AuthURL()

#        return HttpResponse ('{"status": "204", "errorString": "User removed from admins"}',
#                  content_type='application/json', status=204)

def _deleteSupportIrods(request, token, authuser, newuser):
    with GetSession(token, authuser) as session:
        try:
            group.remove_user_from_lexis_sup_group(session, newuser)
            # FIXME add federated users in a loop
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_SUCCESS_BUT_WITH_NO_INFO:
          return HttpResponse (status=204)
        return HttpResponse (status=204)

@csrf_exempt
def userIrodsAPI(request):
    (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        newuser=q['username']
        uid=q['id']
      except:
        return MalformedRequest()
      return _createUserIrods(request, dditoken, user, newuser, uid)
    elif request.method=='DELETE':
      try:
        q=json.loads(request.body.decode('utf-8'))
        newuser=q['username']
      except:
        return MalformedRequest()
      return _deleteUserIrods(request, dditoken, user, newuser)
    else:
      return E405()

@csrf_exempt
def adminIrodsAPI(request):
    (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        newuser=q['username']
      except:
        return MalformedRequest()
      return _adminUserIrods(request, dditoken, user, newuser)
    elif request.method=='DELETE':
      try:
        q=json.loads(request.body.decode('utf-8'))
        newuser=q['username']
      except:
        return MalformedRequest()
      return _deleteAdminIrods(request, dditoken, user, newuser)
    else:
      return E405()

@csrf_exempt
def supportIrodsAPI(request):
    (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    if request.method=='POST':
      try:
        q=json.loads(request.body.decode('utf-8'))
        newuser=q['username']
      except:
        return MalformedRequest()
      return _supportUserIrods(request, dditoken, user, newuser)
    elif request.method=='DELETE':
      try:
        q=json.loads(request.body.decode('utf-8'))
        newuser=q['username']
      except:
        return MalformedRequest()
      return _deleteSupportIrods(request, dditoken, user, newuser)
    else:
      return E405()


@login_required
def userIrodsWeb(request):
    return E501Web()

@login_required
def adminIrodsWeb(request):
    return E501Web()

@login_required
def supportIrodsWeb(request):
    return E501Web()


@csrf_exempt
def userIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return userIrodsAPI(request)
    else:
      return userIrodsWeb(request)

@csrf_exempt
def adminIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return adminIrodsAPI(request)
    else:
      return adminIrodsWeb(request)

@csrf_exempt
def supportIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return supportIrodsAPI(request)
    else:
      return supportIrodsWeb(request)


