import pdb
import sys
import logging
import traceback

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .utils import randomString, GetUserAndTokenWeb, GetUserAndTokenAPI, AuthURL, E405, S201

from django.http import HttpResponse

from .settings import IRODS

from irods.access import iRODSAccess
from irods.session import iRODSSession
from irods.manager.collection_manager import CollectionManager
from irods.exception import CollectionDoesNotExist, CAT_NO_ACCESS_PERMISSION, CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME
from irods.models import DataObject, DataObjectMeta, Collection, CollectionMeta

from irods.connection import ExceptionOpenIDAuthUrl

from irodsApisForWp8 import group

logger = logging.getLogger(__name__)

def _initializeIrods(request, token, user):
    with iRODSSession(host=IRODS['host'], port=IRODS['port'], authentication_scheme='openid',
        openid_provider='keycloak_openid', user=user,
        zone=IRODS['zone'], access_token=token,
        block_on_authURL=False
        ) as session:
        try:
          coll_manager = CollectionManager(session)
          coll_manager.create("/"+IRODS['zone']+"/project")
          p=coll_manager.create("/"+IRODS['zone']+"/public")

          acl_public = iRODSAccess('inherit', "/"+IRODS['zone']+"/public")
          session.permissions.set(acl_public, admin=True)

          coll_manager.create("/"+IRODS['zone']+"/user")

          try:
            group.create_lexis_group_(session)
            group.set_lexis_group_rights(session, IRODS['zone'])
            group.create_lexis_sup_group(session)
            group.create_lexis_adm_group(session)
          except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
            return HttpResponse ('{"status": "503", "errorString": "Group lexis already exists"}', content_type='application/json', status=503)
          group.set_lexis_group_rights(session, IRODS['zone'])
        except ExceptionOpenIDAuthUrl:
          return AuthURL()
        except CAT_NO_ACCESS_PERMISSION:
          logger.warning(traceback.format_tb(sys.exc_info()[2]));
          return HttpResponse ('{"status": "403", "errorString": "User not authorized to setup backend"}',
                    content_type='application/json', status=403)


    return S201()

@csrf_exempt
def initializeIrodsAPI(request):
    if request.method!='POST':
       return E405()
    (dditoken, user, refresh, token, attr, resp)=GetUserAndTokenAPI(request)
    if resp is not None:
       return resp
    return _initializeIrods(request, dditoken, user)

@login_required
def initializeIrodsWeb(request):
    (token, user) = GetUserAndTokenWeb(request)
    return _initializeIrods(request, token, user)

def initializeIrods(request):
    if request.content_type=='application/json' or request.content_type=='text/json':
      return initializeIrodsAPI(request)
    else:
      return initializeIrodsWeb(request)
