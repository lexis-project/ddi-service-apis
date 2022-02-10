import binascii
import hashlib
from logging import raiseExceptions
import os
import shutil
from irods.session import iRODSSession
from transfer.systems import systems
import jwt
import base64
from transfer import exceptions


def project_shortname_hash(project):
    """
    Hash project shortname.

    Parameters
    ----------
    project - Lexis project shortname i.e. "testproject"

    Returns
    -------
    Hashed Lexis project shortname.
    """
    return 'proj{0}'.format(hashlib.md5(project.encode()).hexdigest())


def get_irods_path(project, user, access):
    """
    Get path to Lexis iRODS zone

    Parameters
    ----------
    project
    user
    access

    Returns
    -------
    Absolute path to Lexis iRODS zone
    """
    if access == 'user':
        # /<zone>/user/projXXYY/<username>
        return os.path.join(access, project_shortname_hash(project), user)
    else:
        # /<zone>/{public,project}/projXXYY
        return os.path.join(access, project_shortname_hash(project))

def get_username(token):
    """
    Get username from Lexis AAI token
    Parameters
    ----------
    token

    Returns
    -------
    username
    """
    # Get username from token
    dec = jwt.decode(token.encode('utf-8'), verify=False)
    return dec.get('irods_name', dec.get('preferred_username'))


def get_irods_session(token, zone):
    """
    Create iRODS session with OpenID token
    Parameters
    ----------
    token - Lexis AAI token

    Returns
    -------
    iRODSSession
    """
    irods_system = systems['systems'][zone]

    # Create session
    return iRODSSession(
        host=irods_system.get('host'),
        port=irods_system.get('port'),
        authentication_scheme='openid',
        openid_provider='keycloak_openid',
        zone=irods_system.get('zone'),
        access_token=token,
        user=get_username(token),
        block_on_authURL=False)

def get_dataset_encryption_flag(token, zone, project, access, dataset_id):
    session = get_irods_session(token, zone)
    zone_base_path = systems['systems'][zone]['base_path']

    # Absolute path to iRODS
    irods_path = os.path.join(
        zone_base_path,
        get_irods_path(project, get_username(token), access),
        dataset_id
    )

    # Get the encryption flag from the dataset
    dataset_collection = session.collections.get(irods_path)
    encryption_flag = dataset_collection.metadata.get_one("encryption").value
    return encryption_flag == "yes"


# Shamelessly stolen from django-tus code
def get_metadata(request):
    metadata = {}
    try:
        if request.META.get("HTTP_UPLOAD_METADATA"):
            for kv in request.META.get("HTTP_UPLOAD_METADATA").split(","):
                splited_metadata = kv.split(" ")
                if len(splited_metadata) == 2:
                    key, value = splited_metadata
                    value = base64.b64decode(value)
                    if isinstance(value, bytes):
                        value = value.decode()
                    metadata[key] = value
                else:
                    metadata[splited_metadata[0]] = ""
    except binascii.Error as be:
        raise exceptions.TransferInvalidParameter("Invalid Base64 in TUS metadata")
    except KeyError as ke:
        raise exceptions.TransferInvalidParameter("Missing key in TUS metadata: {0 ".format(ke))

    return metadata


def append_tus_meta(meta, key, value):
    encoded = base64.b64encode(value.encode('utf-8')).decode('utf-8')
    item = "{0} {1}".format(key, encoded)
    return "{0},{1}".format(meta, item)