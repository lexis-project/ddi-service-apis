import yaml
from . import irods_transfer
from . import heappe_requests
from . import nfs_transfer
from . import cp_ssh
from . import utils
import copy
import os
import jwt
import sys
import json
import base64
import uuid


with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)

# Class 1


def irods_to_nfs(input_data, clean_source=False, revoke_token=False):
    source_system = input_data["source_system"]
    sys.stdout.write(source_system)
    target_system = input_data["target_system"]
    source_path = input_data["source_path"]
    target_path = input_data["target_path"]
    token = input_data["token"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    target_path_complete = target_info.get("base_path") + target_path
    try:
        session = irods_transfer.get_session(token, source_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    if (irods_transfer.check_collection_exists(session, source_path_complete)
            or irods_transfer.check_object_exists(session, source_path_complete)):
        check_folder = os.path.isdir(target_path_complete)
        sys.stdout.write(str(check_folder))
        if not check_folder:
            sys.stdout.write("Creating target path" + target_path_complete)
            os.makedirs(target_path_complete)
            nfs_transfer.recursive_chmod(target_path_complete)
        transfer = irods_transfer.initiate_irods_to_staging_zone_transfer_refresh(
            token, source_info, source_path_complete, target_path_complete)
    else:
        transfer = None
        session.cleanup()
        raise Exception("Dataset doesn't exist or wrong target path")
    if clean_source:
        irods_transfer.delete_irods_target(session, source_path_complete)
    session.cleanup()
    if revoke_token:
        utils.revokeToken(token)
    nfs_transfer.recursive_chmod(transfer)
    return transfer

# Class 2


def nfs_to_irods(input_data, clean_source=False, revoke_token=False):
    source_system = input_data["source_system"]
    target_system = input_data["target_system"]
    source_path = input_data["source_path"]
    target_path = input_data["target_path"]
    metadata = input_data["metadata"]
    token = input_data["token"]
    enc_flag = input_data["encryption"]
    comp_flag = input_data["compression"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    target_path_complete = target_info.get("base_path") + target_path
    try:
        session = irods_transfer.get_session(token, target_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    sys.stdout.write("starting transfer")
    transfer = irods_transfer.initiate_staging_zone_to_irods_transfer(
        session, source_path_complete, target_path_complete, metadata)
    irods_transfer.assign_encryption_compression_meta(
        session, transfer, enc_flag, comp_flag)
    if clean_source:
        nfs_transfer.delete_nfs_target(source_path_complete)
    session.cleanup()
    if revoke_token:
        utils.revokeToken(token)
    return transfer

# Class 3


def nfs_to_nfs_transfer(input_data, clean_source=False, revoke_token=False):
    source_system = input_data["source_system"]
    target_system = input_data["target_system"]
    source_path = input_data["source_path"]
    target_path = input_data["target_path"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    target_path_complete = target_info.get("base_path") + target_path
    token = input_data["token"]
    transfer = nfs_transfer.initiate_internal_nfs_to_transfer(
        source_path_complete, target_path_complete)
    nfs_transfer.recursive_chmod(target_path_complete)
    if clean_source:
        nfs_transfer.delete_nfs_target(source_path_complete)
    if revoke_token:
        utils.revokeToken(token)
    return transfer

# Class 6


def nfs_to_local_hpc(input_data, clean_source=False, revoke_token=False):
    source_system = input_data["source_system"]
    target_system = input_data["target_system"]
    source_path = input_data["source_path"]
    target_path = input_data["target_path"]
    task_id = input_data["task_id"]
    job_id = input_data["job_id"]
    token = input_data["token"]
    heappe_url = input_data["heappe_url"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    target_path_complete = target_info.get("base_path") + target_path
    user = irods_transfer.get_user(token)
    heappe_auth = heappe_requests.heappe_auth_keycloack(
        token, user, heappe_url)
    if "id" in heappe_auth:
        session_code = (heappe_auth["id"])[1:-1]
        sys.stdout.write("session code: " + str(session_code))
        transfer_data = heappe_requests.get_heappe_file_transfer(
            session_code, job_id, heappe_url)
        sys.stdout.write(str(transfer_data))
        start_transfer = json.loads(transfer_data["Access"])
        sys.stdout.write(str(start_transfer))
        try:
            heappe_target = start_transfer["ServerHostname"]
            heappe_path = start_transfer["SharedBasepath"]
            heappe_full_path = heappe_target + ":/" + target_path
            heappe_user = start_transfer['Credentials']['Username']
            heappe_private_key = start_transfer['Credentials']['PrivateKey']
        except BaseException:
            raise (Exception("HEAppE job ID is invalid"))
    else:
        raise (Exception("HEAppE Authentication failed"))
    try:
        cp_ssh.remote_cp_to_hpc(
            source_path_complete,
            heappe_full_path,
            heappe_user,
            heappe_private_key)
        sys.stdout.write(str(heappe_requests.end_heappe_file_transfer(
            session_code, transfer_data, job_id, heappe_url)))
    except BaseException:
        sys.stdout.write(str(heappe_requests.end_heappe_file_transfer(
            session_code, transfer_data, job_id, heappe_url)))
        raise (Exception("Problem occurred when calling the HEAppE endpoint"))
    if clean_source:
        nfs_transfer.delete_nfs_target(source_path_complete)
    if revoke_token:
        utils.revokeToken(token)
    return heappe_full_path


# Class 7
def local_hpc_to_nfs(input_data, revoke_token=False):
    source_path = input_data["source_path"]
    target_path = input_data["target_path"]
    source_system = input_data["source_system"]
    target_system = input_data["target_system"]
    task_id = input_data["task_id"]
    job_id = input_data["job_id"]
    token = input_data["token"]
    heappe_url = input_data["heappe_url"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    target_path_complete = target_info.get("base_path") + target_path
    user = irods_transfer.get_user(token)
    heappe_auth = heappe_requests.heappe_auth_keycloack(
        token, user, heappe_url)
    if "id" in heappe_auth:
        session_code = (heappe_auth["id"])[1:-1]
        sys.stdout.write("session code: " + str(session_code))
        transfer_data = heappe_requests.get_heappe_file_transfer(
            session_code, job_id, heappe_url)
        sys.stdout.write(str(transfer_data))
        start_transfer = json.loads(transfer_data["Access"])
        sys.stdout.write(str(start_transfer))
        try:
            heappe_target = start_transfer["ServerHostname"]
            heappe_path = start_transfer["SharedBasepath"]
            heappe_full_path = heappe_target + ":/" + source_path
            heappe_user = start_transfer['Credentials']['Username']
            heappe_private_key = start_transfer['Credentials']['PrivateKey']
        except BaseException:
            raise (Exception("HEAppE job ID is invalid"))
    else:
        raise (Exception("HEAppE Authentication failed"))
    sys.stdout.write(heappe_full_path)
    if not os.path.exists(target_path_complete):
        os.mkdir(target_path_complete)
    try:
        cp_ssh.remote_cp_from_hpc(
            heappe_full_path,
            target_path_complete,
            heappe_user,
            heappe_private_key)
        sys.stdout.write(str(heappe_requests.end_heappe_file_transfer(
            session_code, transfer_data, job_id, heappe_url)))
        nfs_transfer.recursive_chmod(target_path_complete)
    except BaseException:
        sys.stdout.write(str(heappe_requests.end_heappe_file_transfer(
            session_code, transfer_data, job_id, heappe_url)))
        raise (Exception("Problem occurred when calling the HEAppE endpoint"))
    target_full_path = target_path_complete + \
        "/" + os.path.basename(source_path)
    if revoke_token:
        utils.revokeToken(token)
    return target_full_path

# Class 4


def irods_to_local_hpc(input_data, revoke_token=False):
    temp_area = systems["local_staging_area"]
    temp_input_data = copy.deepcopy(input_data)
    temp_input_data["target_system"] = temp_area
    temp_input_data["target_path"] = "tmp_staging" + "/" + str(uuid.uuid1())
    transfer = irods_to_nfs(temp_input_data)
    temp2_input_data = copy.deepcopy(input_data)
    temp2_input_data["source_system"] = temp_area
    temp2_input_data["source_path"] = os.path.relpath(
        transfer, systems["systems"][temp_area]["base_path"])
    transfer2 = nfs_to_local_hpc(temp2_input_data, clean_source=True)
    token = input_data["token"]
    if revoke_token:
        utils.revokeToken(token)
    return transfer2

# Class 5


def local_hpc_to_irods(input_data, revoke_token=False):
    temp_area = systems["local_staging_area"]
    temp_input_data = copy.deepcopy(input_data)
    temp_input_data["target_system"] = temp_area
    temp_input_data["target_path"] = "tmp_staging" + "/" + str(uuid.uuid1())
    transfer = local_hpc_to_nfs(temp_input_data)
    temp2_input_data = copy.deepcopy(input_data)
    temp2_input_data["source_system"] = temp_area
    temp2_input_data["source_path"] = os.path.relpath(
        transfer, systems["systems"][temp_area]["base_path"])
    transfer2 = nfs_to_irods(temp2_input_data, clean_source=True)
    token = input_data["token"]
    if revoke_token:
        utils.revokeToken(token)
    return transfer2

# Duplicate


def duplicate(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    token = input_data["token"]
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    try:
        target_system = input_data["target_system"]
        target_path = input_data["target_path"]
        target_info = systems["systems"][target_system]
        target_path_complete = target_info.get("base_path") + target_path
    except BaseException:
        sys.stdout.write("Going with default target")
        target_path_complete = None
    try:
        title = input_data["title"]
    except BaseException:
        sys.stdout.write("Going with default title")
        title = None
    try:
        session = irods_transfer.get_session(token, source_info)
        session.connection_timeout = 43200
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    try:
        duplicate_data = irods_transfer.duplicate_dataset(
            session, source_path_complete, target_path_complete, title)
        session.cleanup()
        utils.revokeToken(token)
        return duplicate_data
    except BaseException:
        session.cleanup()
        utils.revokeToken(token)
        raise


def get_local_irods():
    return systems["local_irods"]


def get_base_path(input_system):
    info = systems["systems"][input_system]
    return info["base_path"]


def prepare_irods_home(token):
    local_zone = systems["local_zone"]
    user = irods_transfer.get_user(token)
    irods_home = "home/" + user
    return irods_home


def prepare_input_to_iRODS(input_data):
    token = input_data["token"]
    input_data["target_system"] = systems["local_irods"]
    input_data["target_path"] = prepare_irods_home(token)
    input_data["metadata"] = systems["metadata"]
    return input_data


def prepare_input_to_iRODS2(transfer_output, input_data):
    token = input_data["token"]
    input_data["target_system"] = systems["local_irods"]
    input_data["target_path"] = prepare_irods_home(token)
    input_data["source_system"] = systems["burst_buffer_area"]
    base_path = get_base_path(systems["burst_buffer_area"])
    source_path = os.path.relpath(transfer_output[1], base_path)
    input_data["source_path"] = source_path
    input_data["metadata"] = systems["metadata"]
    return input_data


def delete_irods(input_data, revoke_token=False):
    target_system = input_data["target_system"]
    target_path = input_data["target_path"]
    token = input_data["token"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    try:
        session = irods_transfer.get_session(token, target_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    if len(target_path_complete.split("/")) > 4:
        irods_transfer.delete_irods_target(session, target_path_complete)
        session.cleanup()
        if revoke_token:
            utils.revokeToken(token)
    else:
        session.cleanup()
        raise Exception("You have no rights to delete this directory")


def delete_nfs(input_data, revoke_token=False):
    target_system = input_data["target_system"]
    target_path = input_data["target_path"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    token = input_data["token"]
    nfs_transfer.delete_nfs_target(target_path_complete)
    if revoke_token:
        utils.revokeToken(token)

def delete_hpc(input_data, revoke_token=False):
    target_system = input_data["target_system"]
    target_path = input_data["target_path"]
    token = input_data["token"]
    heappe_url = input_data["heappe_url"]
    job_id = input_data["job_id"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    user = irods_transfer.get_user(token)
    heappe_auth = heappe_requests.heappe_auth_keycloack(
        token, user, heappe_url)
    if "id" in heappe_auth:
        session_code = (heappe_auth["id"])[1:-1]
        sys.stdout.write("session code: " + str(session_code))
        transfer_data = heappe_requests.get_heappe_file_transfer(
            session_code, job_id, heappe_url)
        sys.stdout.write(str(transfer_data))
        start_transfer = json.loads(transfer_data["Access"])
        sys.stdout.write(str(start_transfer))
        try:
            heappe_target = start_transfer["ServerHostname"]
            heappe_path = start_transfer["SharedBasepath"]
            heappe_full_path = heappe_target + ":/" + target_path
            heappe_user = start_transfer['Credentials']['Username']
            heappe_private_key = start_transfer['Credentials']['PrivateKey']
        except BaseException:
            raise (Exception("HEAppE job ID is invalid"))
    else:
        raise (Exception("HEAppE Authentication failed"))
    cp_ssh.delete_hpc(heappe_full_path, heappe_user, heappe_private_key)
    sys.stdout.write(str(heappe_requests.end_heappe_file_transfer(
        session_code, transfer_data, job_id, heappe_url)))
    if revoke_token:
        utils.revokeToken(token)


def prepare_encryption1(input_data):
    target_system = systems["burst_buffer_area"]
    target_path = "tmp" + "/" + str(uuid.uuid1())
    input_data["target_system"] = target_system
    input_data["target_path"] = target_path
    return input_data


def prepare_encryption3(transfer_output, input_data):
    source_system = systems["burst_buffer_area"]
    base_path = get_base_path(source_system)
    source_path = os.path.relpath(transfer_output[1], base_path)
    input_data["source_system"] = source_system
    input_data["source_path"] = source_path
    return input_data


def prepare_encryption2(transfer_output, input_data):
    temp_input_data = {}
    source_system = systems["burst_buffer_area"]
    sys.stdout.write(source_system)
    base_path = get_base_path(source_system)
    sys.stdout.write(base_path)
    source_path = os.path.relpath(transfer_output[1], base_path)
    sys.stdout.write(source_path)
    temp_input_data["source_system"] = source_system
    temp_input_data["source_path"] = source_path
    temp_input_data["token"] = input_data["token"]
    temp_input_data["secrets"] = input_data["secrets"]
    temp_input_data["project"] = input_data["project"]
    return temp_input_data


def prepare_encryption5(transfer_output, input_data):
    target_system = systems["burst_buffer_area"]
    target_path = "tmp" + "/" + str(uuid.uuid1())
    input_data["target_system"] = target_system
    input_data["target_path"] = target_path
    comp = transfer_output[1].split("/")
    zone = '/' + comp[1] + '/'
    base_path = transfer_output[1].replace(zone, '')
    input_data["source_path"] = base_path
    machines = systems["systems"]
    for machine in machines:
        if machines[machine]["base_path"] == zone:
            input_data["source_system"] = machine
    return input_data


def move_nfs(input_data, revoke_token=False):
    source_system = input_data["source_system"]
    target_system = input_data["target_system"]
    source_path = input_data["source_path"]
    target_path = input_data["target_path"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    target_path_complete = target_info.get("base_path") + target_path
    sys.stdout.write(source_path_complete)
    sys.stdout.write(target_path_complete)
    token = input_data["token"]
    transfer = nfs_transfer.move_data(
        source_path_complete, target_path_complete)
    nfs_transfer.recursive_chmod(transfer)
    if revoke_token:
        utils.revokeToken(token)
    return transfer


def get_project_from_source(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    source_info = systems["systems"][source_system]
    sys.stdout.write(str(source_info))
    source_path_complete = source_info.get("base_path") + source_path
    sys.stdout.write(source_path_complete)
    token = input_data["token"]
    try:
        session = irods_transfer.get_session(token, source_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    project = utils.getProjectFromiRODSPath(session, source_path_complete)
    session.cleanup()
    return project


def get_project_from_target(input_data):
    target_system = input_data["target_system"]
    target_path = input_data["target_path"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    token = input_data["token"]
    try:
        session = irods_transfer.get_session(token, target_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    project = utils.getProjectFromiRODSPath(session, target_path_complete)
    session.cleanup()
    return project


def get_random_key_and_apppend(secrets):
    message = os.urandom(32).hex()
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    passphrase = base64_bytes.decode('ascii')
    project = "user"
    user_dict = {"PRJ": project, "PASSPHRASE": passphrase}
    secrets.append(user_dict)
    return secrets


def get_enc_comp_flags(input_data):
    target_system = input_data["target_system"]
    target_path = input_data["target_path"]
    token = input_data["token"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    try:
        session = irods_transfer.get_session(token, target_info)
        flags = irods_transfer.get_encryption_compression_meta(
            session, target_path_complete)
        session.cleanup()
        return flags
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
