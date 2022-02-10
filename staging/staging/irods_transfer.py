from irods.session import iRODSSession
import irods.exception as iRODSExceptions
from irods.connection import ExceptionOpenIDAuthUrl
from shutil import rmtree
import os
import sys
import time
import uuid
import json
import jwt


def get_user(token):
    sys.stdout.write(token)
    dec = jwt.decode(token.encode('utf-8'), verify=False)
    user = dec.get('irods_name', dec.get('preferred_username'))
    sys.stdout.write(user)
    return user


def get_session(token, system_info):
    user = get_user(token)
    session = iRODSSession(
        host=system_info.get('host'),
        port=system_info.get('port'),
        authentication_scheme='openid',
        openid_provider='keycloak_openid',
        zone=system_info.get('zone'),
        access_token=token,
        user=user,
        block_on_authURL=False)
    return session


def check_collection_exists(session, irods_path):
    try:
        session.collections.get(irods_path)
        return True
    except iRODSExceptions.CollectionDoesNotExist:
        sys.stdout.write(
            "Dataset does not exist or insufficient permissions \n")
        return False
    except Exception as e:
        sys.stdout.write(str(e))
        return False


def check_object_exists(session, irods_path):
    try:
        session.data_objects.get(irods_path)
        return True
    except iRODSExceptions.DataObjectDoesNotExist:
        sys.stdout.write(
            "Dataset does not exist or insufficient permissions \n")
        return False
    except Exception as e:
        sys.stdout.write(str(e))
        return False


def has_subcollection(collection):
    """Check if an iRODS Collection has Subcollections.

    Parameters
    ----------
    collection : iRODS collection object
        An iRODS object referring to a collection.
    """
    if len(collection.subcollections) == 0:
        return False
    return True


def has_objects(coll):
    if len(coll.data_objects) == 0:
        return False
    return True


def line_out(s):
    # http://www.termsys.demon.co.uk/vtansi.htm
    sys.stdout.write('\x1b[2K\r')
    sys.stdout.write(str(s))
    sys.stdout.flush()


def coll_size(session, source_path):
    """Recursively get the size of a dataset in bytes.

    Parameters
    ----------
    session : iRODS object
        A session iRODS object to access iRODS.
    source_path : String
        The source path of the dataset
    """
    try:
        coll = session.collections.get(source_path)
    except iRODSExceptions.CollectionDoesNotExist:
        return -1
    if has_objects(coll):
        size = 0
        for obj in coll.data_objects:
            size = size + obj.size
            sys.stdout.write(obj.name)
    if has_subcollection(coll):
        if 'size' not in locals():
            size = 0
        for col in coll.subcollections:
            size = size + coll_size(session, col.path)
            sys.stdout.write(col.name)
    elif not has_objects(coll) and not has_subcollection(coll):
        size = 0
    return size


def coll_files(session, source_path):
    """Recursively get the number of files in a dataset.

    Parameters
    ----------
    session : iRODS object
        A session iRODS object to access iRODS.
    source_path : String
        The source path of the dataset
    """
    try:
        coll = session.collections.get(source_path)
    except iRODSExceptions.CollectionDoesNotExist:
        return -1
    if has_objects(coll):
        if 'file' not in locals():
            file = 0
        file = len(coll.data_objects)
        sys.stdout.write(str(file))
    if has_subcollection(coll):
        for col in coll.subcollections:
            if 'file' not in locals():
                file = 0
            file = file + coll_files(session, col.path)
            sys.stdout.write(col.name)
    elif not has_objects(coll) and not has_subcollection(coll):
        file = 0
    return file


def coll_smallfiles(session, source_path):
    """Recursively get the number of small files in a dataset.

    Parameters
    ----------
    session : iRODS object
        A session iRODS object to access iRODS.
    source_path : String
        The source path of the dataset
    """
    try:
        coll = session.collections.get(source_path)
    except iRODSExceptions.CollectionDoesNotExist:
        return -1
    if has_objects(coll):
        if 'smallfile' not in locals():
            smallfile = 0
        for obj in coll.data_objects:
            if obj.size < 33554432:
                smallfile += 1
    if has_subcollection(coll):
        for col in coll.subcollections:
            if 'smallfile' not in locals():
                smallfile = 0
            smallfile = smallfile + coll_smallfiles(session, col.path)
    elif not has_objects(coll) and not has_subcollection(coll):
        smallfile = 0
    return smallfile


def set_metadata(coll, metadata):
    # pdb.set_trace()
    metadataSingleValue = [
        'identifier',
        'title',
        'publicationYear',
        'resourceType',
        'resourceTypeGeneral',
        'CustomMetadata',
        'scope',
        'format']
    metadataMultiValue = [
        'creator',
        'publisher',
        'owner',
        'contributor',
        'relatedIdentifier',
        'rights',
        'rightsURI',
        'rightsIdentifier',
        'CustomMetadataSchema',
        'AlternateIdentifier',
        'RelatedSoftware',
        'description']

    sys.stdout.write(str(metadata))
    for x in metadataSingleValue:
        try:
            val = metadata[x]
            if x == "CustomMetadata":
                coll.metadata.add(x, json.dumps(val))
            else:
                coll.metadata.add(x, str(val))
        except BaseException:
            sys.stdout.write('Metadata for ' + x + ' missing')
        # return error later or add to warning list

    for x in metadataMultiValue:
        try:
            val = metadata[x]
            if not isinstance(val, str):
                for y in val:
                    if x == "CustomMetadataSchema" or x == "AlternateIdentifier":
                        coll.metadata.add(x, json.dumps(y))
                    else:
                        coll.metadata.add(x, str(y))
        except BaseException:
            sys.stdout.write('Metadata for ' + x + ' missing or not array')

#https://github.com/irods/python-irodsclient/issues/320
def tiering_get_object(session, source_path, target_path):
    try:
        session.data_objects.get(source_path)
        session.data_objects.get(source_path, target_path)
    except CAT_NO_ACCESS_PERMISSION as e:
        if not str(e).startswith ("failed to set access time for"):
            raise str(e)

def iget(session, source_path):
    coll = session.collections.get(source_path)
    temp = coll.name
    os.mkdir(temp)
    os.chdir(temp)
    if has_objects(coll):
        for obj in coll.data_objects:
            dirpath = os.getcwd() + "/" + obj.name
            tiering_get_object(session, obj.path, dirpath)
    if has_subcollection(coll):
        for col in coll.subcollections:
            iget(session, col.path)
            os.chdir("..")


def initiate_irods_to_staging_zone_transfer(session, source_path, target_path):
    sys.stdout.write(target_path)
    try:
        os.chdir(target_path)
    except BaseException:
        raise NotADirectoryError
    try:
        sys.stdout.write("A " + source_path)
        session.collections.get(source_path)
        sys.stdout.write("B")
        iget(session, source_path)
        sys.stdout.write("C")
        return target_path
    except iRODSExceptions.CollectionDoesNotExist:
        try:
            sys.stdout.write("D")
            tiering_get_object(session, source_path, target_path)
            sys.stdout.write("E")
            return target_path
        except BaseException:
            sys.stdout.write("N")
            raise (Exception("Permission Denied"))
    except ExceptionOpenIDAuthUrl:
        sys.stdout.write("F")
        raise (Exception("Token not accepted by irods: token not valid or not validated by broker. Or user unknown to "
                         "iRODS (Auth URL sent by irods)"))
    except Exception as e:
        sys.stdout.write("G")
        sys.stdout.write(str(e))
        raise (Exception("Irods path does not exist, " + str(e)))


def initiate_staging_zone_to_irods_transfer(
        session, source_path, target_path, metadata=None):
    created = False
    if len(target_path.split("/")) == 4:
        target_root_dir = target_path + "/" + str(uuid.uuid1())
        temp_root_dir = session.collections.create(target_root_dir)
        created = True
        sys.stdout.write("New random collection created \n")
    else:
        target_root_dir = target_path
        try:
            if not check_collection_exists(session, target_root_dir):
                session.collections.create(target_root_dir)
            temp_root_dir = session.collections.get(target_root_dir)
        except iRODSExceptions.CollectionDoesNotExist:
            sys.stdout.write(
                "Dataset does not exist or insufficient permissions \n")
            raise (Exception("Dataset does not exist or insufficient permissions"))
    if metadata is not None:
        set_metadata(temp_root_dir, metadata)
    final_target = target_root_dir
    sys.stdout.write("Start data transfer to " + str(final_target) + "\n")
    try:
        sys.stdout.write("Transfering from: " + source_path + "\n")
        if os.path.isdir(source_path):
            for subdir, dirs, files in os.walk(source_path):
                for coll_dir in dirs:
                    full_path = os.path.join(subdir, coll_dir)
                    abs_path = full_path.replace(source_path, '')
                    target_dir = target_root_dir + abs_path
                    sys.stdout.write("root_dir is: " + str(target_dir) + "\n")
                    temp_root_dir = session.collections.create(target_dir)
                    sys.stdout.write(str(temp_root_dir.name))
                for filename in files:
                    full_path = os.path.join(subdir, filename)
                    abs_file = full_path.replace(source_path, '')
                    target_file = target_root_dir + abs_file
                    session.data_objects.put(full_path, target_file)
        elif os.path.isfile(source_path):
            sys.stdout.write("Transfering the object: " + source_path + "\n")
            sys.stdout.write(
                "Object to be created is: " +
                final_target +
                "/" +
                os.path.basename(source_path) +
                "\n")
            obj_target = final_target + "/" + os.path.basename(source_path)
            session.data_objects.put(source_path, obj_target)
            final_target = final_target + "/" + os.path.basename(source_path)
        else:
            raise (Exception("Source path doesn't exist"))
    except iRODSExceptions.CollectionDoesNotExist:
        if created:
            temp_root_dir.remove(recurse=True, force=True)
            raise (Exception("Error copying to DDI, possibly wrong source path"))
    return final_target


def delete_coll(session, coll_path):
    try:
        sys.stdout.write("A")
        dataset = session.collections.get(coll_path)
        sys.stdout.write(coll_path)
        sys.stdout.write("B")
        sys.stdout.write(dataset.name)
        dataset.remove(recurse=True, force=True)
        sys.stdout.write("Dataset deleted")
    except iRODSExceptions.CollectionDoesNotExist:
        try:
            file = session.data_objects.get(coll_path)
            file.unlink(force=True)
        except BaseException:
            raise (
                Exception("Dataset or file does not exist or insufficient permissions"))
    except iRODSExceptions.CAT_NO_ACCESS_PERMISSION:
        raise (Exception("Insufficient permissions, possible iRODS misconfiguration"))


def iget2(token, system_info, source_path):
    time.sleep(1)
    session = get_session(token, system_info)
    coll = session.collections.get(source_path)
    temp = coll.name
    if os.path.exists(temp):
        sys.stdout.write("Target exists. Removing it before transfer")
        rmtree(temp)
    else:
        os.mkdir(temp)
        os.chdir(temp)
    if has_objects(coll):
        for obj in coll.data_objects:
            dirpath = os.getcwd() + "/" + obj.name
            tiering_get_object(session, obj.path, dirpath)
    if has_subcollection(coll):
        for col in coll.subcollections:
            sys.stdout.write(col.path)
            iget2(token, system_info, col.path)
            os.chdir("..")


def initiate_irods_to_staging_zone_transfer_refresh(
        token, system_info, source_path, target_path):
    sys.stdout.write(target_path)
    try:
        os.chdir(target_path)
    except BaseException:
        raise NotADirectoryError
    try:
        sys.stdout.write("A " + source_path)
        session = get_session(token, system_info)
        session.collections.get(source_path)
        sys.stdout.write("B")
        iget2(token, system_info, source_path)
        sys.stdout.write("C")
        basename = os.path.basename(source_path)
        session.cleanup()
        return target_path + "/" + basename
    except iRODSExceptions.CollectionDoesNotExist:
        try:
            sys.stdout.write("D")
            session = get_session(token, system_info)
            tiering_get_object(session, source_path, target_path)
            obj = session.data_objects.get(source_path)
            sys.stdout.write("E")
            session.cleanup()
            return target_path + "/" + obj.name
        except BaseException:
            sys.stdout.write("N")
            raise (Exception("Permission Denied"))
    except ExceptionOpenIDAuthUrl:
        sys.stdout.write("F")
        raise (Exception("Token not accepted by irods: token not valid or not validated by broker. Or user unknown to "
                         "iRODS (Auth URL sent by irods)"))
    except BaseException:
        sys.stdout.write("G")
        raise (Exception("Irods path does not exist"))


def check_parent_dir(session, dir_path):
    if dir_path is "/":
        sys.stdout.write("Search completed. No PID found")
    else:
        try:
            sys.stdout.write(dir_path)
            coll = session.collections.get(dir_path)
            if "PID" in coll.metadata.keys():
                raise (
                    Exception(
                        str("Data can't be deleted. A PID is already assigned to a parent dir.")))
            parent = os.path.dirname(dir_path)
            sys.stdout.write(parent)
            check_parent_dir(session, parent)
        except iRODSExceptions.CollectionDoesNotExist:
            sys.stdout.write("Search completed. No PID found")


def delete_irods_target(session, target_path):
    try:
        coll = session.collections.get(target_path)
        print(coll.metadata.keys())
        if "PID" in coll.metadata.keys():
            raise (
                Exception(
                    str("Dataset can't be deleted. A PID is already assigned to it.")))
        coll.remove()
    except iRODSExceptions.CollectionDoesNotExist:
        try:
            obj = session.data_objects.get(target_path)
            dir_name = os.path.dirname(target_path)
            check_parent_dir(session, dir_name)
            obj.unlink()
        except iRODSExceptions.DataObjectDoesNotExist:
            sys.stdout.write(
                str("Failed to delete data. Please check iRODS permission or if the data exists"))
            raise (
                Exception(
                    str("Failed to delete data. Please check iRODS permission or if the data exists")))
    except Exception as e:
        sys.stdout.write(
            "Failed to delete data. Please check iRODS permission or if the data exists" +
            str(e))
        raise (
            Exception(
                "Failed to delete data. Please check iRODS permission or if the data exists" +
                str(e)))


def assign_encryption_compression_meta(
        session, dataset_coll, enc_flag, comp_flag):
    try:
        if check_object_exists(session, dataset_coll):
            dataset_coll = os.path.dirname(dataset_coll)
        dataset = session.collections.get(dataset_coll)
        if "encryption" not in dataset.metadata.keys():
            dataset.metadata.add("encryption", enc_flag)
        if "compression" not in dataset.metadata.keys():
            dataset.metadata.add("compression", comp_flag)
    except BaseException:
        raise (Exception("Failed to set encryption and compression flags"))


def get_encryption_compression_meta(session, dataset_coll):
    try:
        dataset = session.collections.get(dataset_coll)
        enc_flag = dataset.metadata.get_one("encryption").value
        comp_flag = dataset.metadata.get_one("compression").value
        return [enc_flag, comp_flag]
    except BaseException:
        return ["encryption flag doesn't exist or dataset doesn't exist",
                "compression flag doesn't exist or dataset doesn't exist"]


def coll_copy(session, source_path, target_path):
    coll_source = session.collections.get(source_path)
    session.collections.create(target_path)
    if has_objects(coll_source):
        for obj in coll_source.data_objects:
            session.data_objects.copy(obj.path, target_path)
    if has_subcollection(coll_source):
        for col in coll_source.subcollections:
            temp_source = col.path
            temp_target = target_path + "/" + col.name
            sys.stdout.write("temp_source: " + temp_source)
            sys.stdout.write("temp_target: " + temp_target)
            coll_copy(session, temp_source, temp_target)


def duplicate_dataset(session, source, target=None, title=None):
    if target is None:
        target = os.path.dirname(source) + "/" + str(uuid.uuid1())
    else:
        target = target + "/" + str(uuid.uuid1())
    try:
        coll_source = session.collections.get(source)
        coll_target = session.collections.create(target)
    except BaseException:
        raise (Exception("Source doesn't exist or can't duplicate to target"))
    try:
        coll_copy(session, source, target)
    except BaseException:
        raise (Exception("Duplication failed"))
    for meta in coll_source.metadata.items():
        try:
            if "EUDAT" not in meta.name and "PID" not in meta.name and "title" not in meta.name:
                coll_target.metadata.add(str(meta.name), str(meta.value))
            if "title" in meta.name:
                if title is None:
                    title = "Duplicate of " + str(meta.value)
                coll_target.metadata.add(str(meta.name), title)
        except BaseException:
            raise (Exception("Couldn't set metadata in target directory"))
    return target
