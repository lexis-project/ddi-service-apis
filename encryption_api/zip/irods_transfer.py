from irods.session import iRODSSession
import irods.exception as iRODSExceptions
from irods.connection import ExceptionOpenIDAuthUrl
from shutil import rmtree
import os
import sys
import time
import humanize
import uuid
import pdb
import json
import jwt

def get_user(token):
    sys.stdout.write(token)
    dec=jwt.decode (token.encode('utf-8'), verify=False)
    user=dec.get('irods_name', dec.get('preferred_username'))
    sys.stdout.write(user)
    return user

def get_session(token, system_info):
    user = get_user(token)
    session = iRODSSession(host=system_info.get('host'), port=system_info.get('port'), authentication_scheme='openid',
         openid_provider='keycloak_openid',
        zone=system_info.get('zone'), access_token=token, user=user,
        block_on_authURL=False)
    return session

def check_collection_exists(session, irods_path):
    try:
      coll = session.collections.get(irods_path)
      return True
    except iRODSExceptions.CollectionDoesNotExist:
      sys.stdout.write("Dataset does not exist or insufficient permissions \n")
      return False
    except Exception as e:
      sys.stdout.write(str(e))
      return False

def check_object_exists(session, irods_path):
    try:
      obj = session.data_objects.get(irods_path)
      return True
    except iRODSExceptions.DataObjectDoesNotExist:
      sys.stdout.write("Dataset does not exist or insufficient permissions \n")
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
    if(len(coll.data_objects) == 0):
        return False
    return True

def line_out(s):
    # http://www.termsys.demon.co.uk/vtansi.htm
    sys.stdout.write('\x1b[2K\r')
    sys.stdout.write(str(s))
    sys.stdout.flush()


def iget_object(session, source_path):
    sys.stdout.write ("XX")
    sys.stdout.write ("source path is %s" % source_path)
    obj = session.data_objects.get(source_path)
    sys.stdout.write ("AA")
    window_start = 0.0
    window_bytes = 0.0
    total_bytes = 0
    average_rate = 0.0
    check_interval = 1.0  # seconds
    dirpath = os.getcwd() + "/" + obj.name
    sys.stdout.write ("BB")
    with obj.open('r') as f_in:
        # 2MiB chunks. Somewhat arbitrary, but pretty good in manual tests
        chunk_size = 2 * 1024 * 1024
        with open(dirpath, 'wb') as f_out:
            window_start = time.time()
            while True:
                sys.stdout.write ("CC")
                chunk = f_in.read(chunk_size)
                if len(chunk) <= 0:
                    break
                total_bytes += len(chunk)
                window_bytes += len(chunk)
                f_out.write(chunk)
                curr_time = time.time()
                if curr_time >= window_start + check_interval:
                    average_rate = 0.6 * average_rate + 0.4 * (window_bytes / (curr_time - window_start))
                    line_out('Total transferred: {} B ({}), Approximate Current Rate: {} B/s ({}/s)'.format(
                        total_bytes, humanize.naturalsize(total_bytes, binary=True),
                        int(average_rate), humanize.naturalsize(average_rate, binary=True)))
                    # reset window stats
                    window_start = time.time()
                    window_bytes = 0.0


def iget2(token, system_info, source_path):
    """Recursively Scan the iRODS Instance for .lrzmetadata.yml Files.

    Parameters
    ----------
    part : String
        A String referring to the path of a collection.
    """
    time.sleep(1)
    session = get_session(token, system_info)
    coll = session.collections.get(source_path)
    temp = coll.name
    if(os.path.exists(temp)):
      sys.stdout.write("Target exists. Removing it before transfer")
      rmtree(temp)
    else:
      os.mkdir(temp)
      os.chdir(temp)
    if has_objects(coll):
        for obj in coll.data_objects:
            window_start = 0.0
            window_bytes = 0.0
            total_bytes = 0
            average_rate = 0.0
            check_interval = 1.0  # seconds
            dirpath = os.getcwd() + "/" + obj.name
            with obj.open('r') as f_in:
                # 8MiB chunks. Somewhat arbitrary, but pretty good in manual tests
                chunk_size = 8 * 1024 * 1024
                with open(dirpath, 'wb') as f_out:
                    sys.stdout.write(dirpath)
                    window_start = time.time()
                    while True:
                        chunk = f_in.read(chunk_size)
                        if len(chunk) <= 0:
                            break
                        total_bytes += len(chunk)
                        window_bytes += len(chunk)
                        f_out.write(chunk)
                        curr_time = time.time()
                        if curr_time >= window_start + check_interval:
                            average_rate = 0.6 * average_rate + 0.4 * (window_bytes / (curr_time - window_start))
                            line_out('Total transferred: {} B ({}), Approximate Current Rate: {} B/s ({}/s)'.format(
                            total_bytes, humanize.naturalsize(total_bytes, binary=True),
                            int(average_rate), humanize.naturalsize(average_rate, binary=True)))
                            # reset window stats
                            window_start = time.time()
                            window_bytes = 0.0
            f_in.close()
            f_out.close()
    if has_subcollection(coll):
        for col in coll.subcollections:
            sys.stdout.write(col.path)
            iget2(token, system_info, col.path)
            os.chdir("..")


def initiate_irods_to_staging_zone_transfer_refresh(token, system_info, source_path, target_path):
    sys.stdout.write(target_path)
    try:
        os.chdir(target_path)
    except:
        raise NotADirectoryError
    try:
        sys.stdout.write ("A "+ source_path)
        session = get_session(token, system_info)
        pcoll = session.collections.get(source_path)
        sys.stdout.write ("B")
        iget2(token, system_info, source_path)
        sys.stdout.write  ("C")
        basename = os.path.basename(source_path)
        return target_path + "/" + basename
    except iRODSExceptions.CollectionDoesNotExist:
        try:
          sys.stdout.write  ("D")
          session = get_session(token, system_info)
          iget_object(session, source_path)
          obj = session.data_objects.get(source_path)
          sys.stdout.write  ("E")
          return target_path + "/" + obj.name
        except:
          sys.stdout.write ("N")
          raise (Exception("Permission Denied"))
    except ExceptionOpenIDAuthUrl:
        sys.stdout.write  ("F")
        raise (Exception("Token not accepted by irods: token not valid or not validated by broker. Or user unknown to iRODS (Auth URL sent by irods)"))
    except:
        sys.stdout.write("G")
        raise (Exception ("Irods path does not exist"))

def irods_to_nfs(input_data):
   source_system = input_data["source_system"]
   sys.stdout.write(source_system)
   target_system = input_data["target_system"]
   source_path = input_data["source_path"]
   target_path = input_data["target_path"]
   token = input_data["token"]
   source_info = systems["systems"][source_system]
   target_info = systems["systems"][target_system]
   source_path_complete= source_info.get("base_path") + source_path
   target_path_complete = target_info.get("base_path") + target_path
   try:
     session = get_session(token, source_info)
   except jwt.exceptions.DecodeError:
     raise Exception("Token Invalid payload")
   if (check_collection_exists(session, source_path_complete) or check_object_exists(session, source_path_complete)):
     CHECK_FOLDER = os.path.isdir(target_path_complete)
     sys.stdout.write(str(CHECK_FOLDER))
     if CHECK_FOLDER == False:
        sys.stdout.write("Creating target path" + target_path_complete)
        os.makedirs(target_path_complete)
     transfer = initiate_irods_to_staging_zone_transfer_refresh(token, source_info, source_path_complete, target_path_complete)
   return transfer
