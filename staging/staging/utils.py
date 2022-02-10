import requests
import yaml
import sys
import json
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode, quote_plus

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)
    keycloak = systems["keycloak"]
    KEYCLOAK_REALM = keycloak["KEYCLOAK_REALM"]
    OIDC_RP_CLIENT_ID = keycloak["OIDC_RP_CLIENT_ID"]
    OIDC_RP_CLIENT_SECRET = keycloak["OIDC_RP_CLIENT_SECRET"]


def requestValidateToken(token):
    microservices = systems["keycloak"]["microservice"]
    for microservice in microservices:
        req = requests.get(
            microservice +
            '/validate_token',
            params={
                'provider': 'keycloak_openid',
                'access_token': token})
        if req.status_code == 200:
            j = req.json()
            if not j['active']:
                return 401
        else:
            return req.status_code
    return 200


def introspect(token):
    res = requests.post(
        KEYCLOAK_REALM +
        '/protocol/openid-connect/token/introspect',
        data='token=' +
        token,
        auth=HTTPBasicAuth(
            OIDC_RP_CLIENT_ID,
            OIDC_RP_CLIENT_SECRET),
        headers={
            'content-type': 'application/x-www-form-urlencoded'})
    if res.status_code != 200:
        return None
    return res.json()


def exchangetoken(token):
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": "urn:ietf:params:oauth:token-type:refresh_token",
        "subject_token": token,
        "scope": "offline_access openid"}
    body = urlencode(params, quote_via=quote_plus)
    res = requests.post(
        KEYCLOAK_REALM +
        '/protocol/openid-connect/token',
        auth=HTTPBasicAuth(
            OIDC_RP_CLIENT_ID,
            OIDC_RP_CLIENT_SECRET),
        data=body,
        headers={
            'content-type': 'application/x-www-form-urlencoded'})
    if res.status_code != 200:
        return None
    return res.json()


def userinfo(token):
    res = requests.post(
        KEYCLOAK_REALM + '/protocol/openid-connect/userinfo',
        data="grant_type=urn:ietf:params:oauth:grant-type:uma-ticket&audience=" + OIDC_RP_CLIENT_ID,
        headers={
            'content-type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + token})
    if res.status_code != 200:
        return None
    return res.json()


def getDDIAttributes(t):
    sys.stdout.write("Initial token is : " + t + "\n")
    i = introspect(t)
    if i is None:
        return None, None, None, None, "Introspect failed"
    if not i["active"]:
        return None, None, None, None, "Inactive token"
    e = exchangetoken(t)
    if e is None:
        return None, None, None, None, "Unable to exchange"
    dditoken = e["access_token"]
    refreshtoken = e["refresh_token"]
    ui = userinfo(dditoken)
    if ui is None:
        return None, None, dditoken, refreshtoken, "Unable to get User Info"
    try:
        a = ui["attributes"]["secrets"]
    except BaseException:
        a = []
    user = ui["preferred_username"]
    res = requestValidateToken(dditoken)
    if res == 200:
        err = None
    else:
        err = "Error connecting to validator service, " + str(res)
    return a, user, dditoken, refreshtoken, err


def getPassword(project, attributes):
    secrets = attributes["secrets"]
    for s in secrets:
        d = json.loads(s)
        if d["PRJ"] == project:
            return d["PASSPHRASE"]

    return None


def getListableProjects(attributes):
    dat_list = attributes["dat_list"]
    projects = []
    for l in dat_list:
        projects.append(l["PRJ"])
    return projects


def getReadableProjects(attributes):
    dat_read = attributes["dat_read"]
    projects = []
    for l in dat_read:
        projects.append(l["PRJ"])
    return projects


def getWritableProjects(attributes):
    dat_write = attributes["dat_write"]
    projects = []
    for l in dat_write:
        projects.append(l["PRJ"])
    return projects


def getProjectFromiRODSPath(session, irodspath):
    comp = irodspath.split("/")
    projpath = '/' + comp[1] + '/' + comp[2] + '/' + comp[3]
    coll = session.collections.get(projpath)
    project = coll.metadata.get_one("ShortProject").value
    return project


def revokeToken(token):
    try:
        res = requests.post(KEYCLOAK_REALM + '/protocol/openid-connect/revoke',
                            data='token=' + token,
                            auth=HTTPBasicAuth(OIDC_RP_CLIENT_ID, OIDC_RP_CLIENT_SECRET),
                            headers={'content-type': 'application/x-www-form-urlencoded'})
        if res.status_code == 200:
            sys.stdout.write("Token revoked")
        else:
            sys.stdout.write("Token revokation failed")
    except:
        sys.stdout.write("Call to revoke the token failed")
