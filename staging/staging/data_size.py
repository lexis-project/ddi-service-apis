from . import irods_transfer
from . import utils
import irods.exception as iRODSExceptions
import yaml
import jwt

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)


def get_data_size(input_data):
    token = input_data["token"]
    target_system = input_data["target_system"]
    target_path = input_data["target_path"]
    target_info = systems["systems"][target_system]
    target_path_complete = target_info.get("base_path") + target_path
    try:
        session = irods_transfer.get_session(token, target_info)
    except jwt.exceptions.DecodeError:
        raise Exception("Token Invalid payload")
    try:
        size = irods_transfer.coll_size(session, target_path_complete)
        allfile = irods_transfer.coll_files(session, target_path_complete)
        smallfile = irods_transfer.coll_smallfiles(
            session, target_path_complete)
        session.cleanup()
        utils.revokeToken(token)
        return [size, allfile, smallfile]
    except iRODSExceptions.CollectionDoesNotExist:
        size = -1
        allfile = -1
        smallfile = -1
        session.cleanup()
        utils.revokeToken(token)
        return [size, allfile, smallfile]
