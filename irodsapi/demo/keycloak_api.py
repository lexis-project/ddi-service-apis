import requests
from keycloak import KeycloakOpenID, KeycloakAdmin
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

def list_user_groups():
    return list_all_users(get_keycloak_admin())

def list_project_groups():
    return list_all_project_groups(get_keycloak_admin())

def get_keycloak_admin():
    return KeycloakAdmin(server_url=settings.KEYCLOAK_ADMIN_URL,
                                   client_id=settings.KEYCLOAK_SERVICE_CLIENT,
                                   client_secret_key=settings.KEYCLOAK_SERVICE_SECRET,
                                   realm_name=settings.KEYCLOAK_ADMIN_REALM,
                                   verify=True)

def get_user_groups(keycloak_admin, userid):
    token = keycloak_admin.token['access_token']
    req = requests.get(settings.KEYCLOAK_ADMIN_URL + "admin/realms/LEXIS_AAI/users/{0}/groups".format(userid),
                       headers={'Authorization': 'Bearer {0}'.format(token),
                                'Content-type': 'application/json'})
    return req.json()

def get_group_details(keycloak_admin, groupid):
    token = keycloak_admin.token['access_token']
    req = requests.get(settings.KEYCLOAK_ADMIN_URL + "admin/realms/LEXIS_AAI/groups/{0}".format(groupid),
                       headers={'Authorization': 'Bearer {0}'.format(token),
                                'Content-type': 'application/json'})
    return req.json()

def get_group_attributes(keycloak_admin, groupid):
    """
    :param keycloak_admin: KC admin
    :param groupid: ID of a group in Keycloak
    :return: dictionary with attr name and its value
    """
    details = get_group_details(keycloak_admin, groupid)

    group_attributes = {}
    for attr_name, attr_value in details['attributes'].items():
        group_attributes[attr_name] = json.loads(attr_value[0])
    return group_attributes

def list_all_project_groups(keycloak_admin):
    """
    :param keycloak_admin: KeycloakAdmin
    :return: List of all project shortnames with at least one record in the DAT_WRITE subgroup
    array of dicts { 'shortname' : <project shortname>, 'uuid': <the uuid>}
    """
    token = keycloak_admin.token['access_token']
    req = requests.get(settings.KEYCLOAK_ADMIN_URL + "admin/realms/LEXIS_AAI/groups",
                       params={"search": "Projects"},
                       headers={'Authorization': 'Bearer {0}'.format(token),
                                'Content-type': 'application/json'})
    groups = req.json()

    project_groups = []
    for project_group in groups[0]['subGroups']:

        for subgroup in project_group['subGroups']:
            if subgroup['name'] == 'DAT':
                # Get attributes for first DAT subgroup
                for datgroup in subgroup['subGroups']:
                    if datgroup['name'] == 'DAT_WRITE' and len(datgroup['subGroups']) > 0:
                        detail = get_group_details(keycloak_admin, datgroup['subGroups'][0]['id'])
                        try:
                            attrs = json.loads(detail['attributes']['DAT_WRITE'][0])
                        except KeyError as e:
                            logger.error("Group {0} does not have attribute DAT_WRITE".format(project_group['name']))
                        project_groups.append({'prj': attrs['PRJ'], 'uuid': attrs['PRJ_UUID']})
    return project_groups

def list_all_users(keycloak_admin):
    """
      :param keycloak_admin: KeycloakAdmin
      :return: List of all users in the realm and their groups
      array of dicts { 'name' : <username>, 'groups': [list of GroupRepresentation]}
      """
    users = keycloak_admin.get_users({})
    user_details = {}
    for user in users:
        groups = get_user_groups(keycloak_admin, user['id'])
        user_details[user['username']] = {'id': user['id'], 'groups': groups}
    return user_details