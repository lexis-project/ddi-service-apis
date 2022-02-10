from . import b2safe_replicate
from . import irods_transfer
from . import utils
import irods.exception as iRODSExceptions
import jwt
import sys
import yaml

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)


def initiate_replication(input_data):
    source_system = input_data["source_system"]
    target_system = input_data["target_system"]
    source_path = input_data["source_path"]
    token = input_data["token"]
    source_info = systems["systems"][source_system]
    target_info = systems["systems"][target_system]
    source_path_complete = source_info.get("base_path") + source_path
    if "user" in source_path_complete:
        raise (Exception("User private data can't be replicated"))
    try:
        target_path = input_data["target_path"]
        target_path_complete = target_info.get("base_path") + target_path
    except BaseException:
        target_path_complete = target_info.get("base_path") + source_path
    try:
        session = irods_transfer.get_session(token, source_info)
        session.connection_timeout = 43200
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    try:
        replicate = b2safe_replicate.replicate(
            session, source_path_complete, target_path_complete)
        session.cleanup()
        utils.revokeToken(token)
        return replicate
    except BaseException:
        utils.revokeToken(token)
        raise


def initiate_pid_assignment(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    source_info = systems["systems"][source_system]
    token = input_data["token"]
    source_path_complete = source_info.get("base_path") + source_path
    if "user" in source_path_complete:
        raise (Exception("User private data can't be assigned a PID"))
    try:
        parent_pid = input_data["parent_pid"]
    except BaseException:
        parent_pid = None
        sys.stdout.write("Assigning PID with no parent PID set")
    try:
        session = irods_transfer.get_session(token, source_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    try:
        assign_pid = b2safe_replicate.assign_pid(
            session, source_path_complete, parent_pid)
        session.cleanup()
        utils.revokeToken(token)
        return assign_pid
    except BaseException:
        utils.revokeToken(token)
        raise


def check_replication(input_data):
    token = input_data["token"]
    target_path = input_data["target_path"]
    target_system = input_data["target_system"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    try:
        session = irods_transfer.get_session(token, target_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    try:
        coll_destination = session.collections.get(target_path_complete)
        try:
            coll_destination.metadata.get_one("EUDAT/REPLICA")
            status = "Parent dataset. Dataset is replicated"
            session.cleanup()
            return status
        except KeyError:
            try:
                coll_destination.metadata.get_one("EUDAT/PARENT")
                status = "Replica dataset. Dataset is replicated"
                session.cleanup()
                return status
            except KeyError:
                status = "Dataset is not replicated"
                return status
    except iRODSExceptions.CollectionDoesNotExist:
        status = "Dataset doesn't exist or you don't have permission to access it"
        return status
