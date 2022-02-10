from base64 import decode
from math import perm
import requests
import yaml
import sys
import json
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode, quote_plus
from transfer import systems
from transfer import exceptions
import logging
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError

logger = logging.getLogger(__name__)

def get_keycloak_client():
     # Get Keycloak client
    return KeycloakOpenID(
        server_url=systems.systems['keycloak']['KEYCLOAK_URL'],
        realm_name=systems.systems['keycloak']['KEYCLOAK_REALM_NAME'],
        client_id=systems.systems['keycloak']['OIDC_RP_CLIENT_ID'],
        client_secret_key=systems.systems['keycloak']['OIDC_RP_CLIENT_SECRET']
    )


def authorize_request(token, project, permission):
    """
    Used to check if a token is valid and has proper permissions for the project given the permisssion (DAT_READ or DAT_WRITE)
    """
    try:
        keycloak = get_keycloak_client()
        
        # Check if user has correct permission
        project_perms = keycloak.userinfo(token)['attributes'].get(permission)
        if not project_perms:
            logger.error("Permission {0} not found in user attribute".format(permission))
            raise exceptions.TransferUnauthorized
        
        # Look for corresponding project
        found = False
        for perm in project_perms:
            if perm['PRJ'] == project:
                found = True
                break
         
        if found:
            # Validate token on all iRODS brokers
            for broker in systems.systems["keycloak"]["microservice"]:
                req = requests.get(broker + '/validate_token',
                            params={'provider': 'keycloak_openid',
                                    'access_token': token})
                if req.status_code == 200:
                    # Broker should return active: True in the response
                    try:
                        if not req.json()['active']:
                            raise exceptions.TransferUnauthorized
                    except KeyError as ke:
                        logger.error("Invalid response from iRODS broker {0} - {1}".format(broker, req.text))
                else:
                    logger.error("Unable to validate token on iRODS broker {0} - {1}".format(broker, req.text))
                    raise exceptions.TransferError
        else:
            # Raise unauthorized by default
            logger.error("Permission {0} not found for project {1}".format(permission, project))
            raise exceptions.TransferUnauthorized

    except KeycloakError as ke:
        logger.error("Error when connecting to Keycloak: {0}".format(ke))
        raise exceptions.TransferError

def authentize_request(request, token=None):
    """
    Checks if token is valid and active, raises TransferUnauthorized if not
    """
    try:
        keycloak = get_keycloak_client()

        if not token:
            # Extract token from Authorization: Bearer <token> header
            token = request.headers.get('Authorization')
            
        if not token:
            logger.error("Authorization header not found.")
            raise exceptions.TransferUnauthorized

        try:
            token = token.split(' ')[1] 
        except IndexError:
            logger.error("Invalid format of Authorization header: {0}".format(token))
 
        # Get username
        decoded = keycloak.decode_token(token=token, key=None, options={"verify_signature": False})
        username = decoded['preferred_username']

        # Check if token is active
        if not keycloak.introspect(token)['active']:
            logger.error("Token is not active for user {0}".format(username))
            raise exceptions.TransferUnauthorized
        else:
            return (token, username)

    except KeycloakError as ke:
        logger.error("Authentize: Keycloak error - {0}").format(ke)
        raise exceptions.TransferError


def exchange_token(token):
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": "urn:ietf:params:oauth:token-type:refresh_token",
        "subject_token": token,
        "scope": "offline_access openid"}
    body = urlencode(params, quote_via=quote_plus)
    res = requests.post(
        systems.systems["keycloak"]["KEYCLOAK_REALM"] +
        '/protocol/openid-connect/token',
        auth=HTTPBasicAuth(
           systems.systems["keycloak"]["OIDC_RP_CLIENT_ID"] ,
            systems.systems["keycloak"]["OIDC_RP_CLIENT_SECRET"]),
        data=body,
        headers={
            'content-type': 'application/x-www-form-urlencoded'})
    if res.status_code != 200:
        return None
    return res.json()['access_token']


def get_secrets(token):
    """
    Returns secrects stored in group attributes
    """
    try:
        return get_keycloak_client().userinfo(token)['attributes'].get('secrets')
    except KeycloakError as ke:
        logger.error("Keycloak error: {0}").format(ke)
        raise exceptions.TransferError
    except KeyError as ke:
        logger.error("Secrects not found in token.")
        raise exceptions.TransferUnauthorized