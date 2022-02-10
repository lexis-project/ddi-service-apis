import logging
import re
from transfer import exceptions
from transfer import systems
import uuid
import json

logger = logging.getLogger(__name__)

def valid_string(string):
    expr = re.compile('^[\w_\-\/\.]+$')
    return expr.match(string)

def check_missing_keys(request, required):
    missing = []
    try:
        for key in required:
            value = request[key]
    except KeyError as ke:
        missing.append(ke)
           
    if missing:
        logger.error("Missing keys: {0}".format(missing))
        raise exceptions.TransferInvalidParameter("Missing keys: {0}".format(missing))

def check_irods_zone(zone):
    if not systems.find_system_by_zone(zone):
        raise exceptions.TransferInvalidParameter("Invalid zone: {0}".format(zone))

def check_access(access):
    allowed = ['project','public', 'project']
    if access not in allowed:
        raise exceptions.TransferInvalidParameter("Invalid access: {0}".format(access))

def check_path(path):
    if not valid_string(path):
        raise exceptions.TransferInvalidParameter("Invalid path: {0}".format(path))

def check_uuid(uuid_string):
    try:
        uuid_obj = uuid.UUID(uuid_string)
    except ValueError as ve:
        raise exceptions.TransferInvalidParameter("Invalid UUID: {0}".format(uuid_string))

def check_bool(bool_string):
    if bool_string not in ['yes', 'no']:
        raise exceptions.TransferInvalidParameter("Invalid boolean value: {0}".format(bool_string))

# Validate data from views
# TODO: Add metadata validation

def upload(request_data):
    required_keys = ['zone', 'access', 'project', 'path', 'token', 'metadata', 'encryption', 'expand', 'filename']
    check_missing_keys(request_data, required_keys)

    check_access(request_data['access'])
    check_irods_zone(request_data['zone'])
    
    # Path can be empty
    if len(request_data['path']) > 0:
        check_path(request_data['path'])
    
    # Dataset is optional
    if  'dataset_id' in request_data:
        check_uuid(request_data['dataset_id'])

    valid_string(request_data['filename'])
    check_bool(request_data['encryption'])
    check_bool(request_data['expand'])

    # Try to decode metadata and validate them
    try:
        meta = json.loads(request_data['metadata'])
    except json.JSONDecodeError as je:
        logger.error("Cannot decode dataset metadata JSON: {0}".format(je))
        raise exceptions.TransferInvalidParameter("Invalid dataset metadata JSON")
    


def download(request_data):
    required_keys = ['zone', 'access', 'project', 'dataset_id', 'path']
    check_missing_keys(request_data, required_keys)

    # Validate them
    check_access(request_data['access'])
    check_irods_zone(request_data['zone'])
    check_path(request_data['path'])
    check_uuid(request_data['dataset_id'])

