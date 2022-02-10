from irods.session import iRODSSession
from irods.access import iRODSAccess
import irods.exception as iRODSExceptions
import os
import sys
import time
import humanize


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

def iget(session, source_path):
    """Recursively Scan the iRODS Instance for .lrzmetadata.yml Files.

    Parameters
    ----------
    part : String
        A String referring to the path of a collection.
    """
    coll = session.collections.get(source_path)
    temp = coll.name
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
                # 2MiB chunks. Somewhat arbitrary, but pretty good in manual tests
                chunk_size = 2 * 1024 * 1024
                with open(dirpath, 'wb') as f_out:
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
    if has_subcollection(coll):
        for col in coll.subcollections:
            iget(session, col.path)
            os.chdir("..")


def initiate_irods_to_staging_area_transfer(session, source_path, target_system, target_path):
    try:
        coll = session.collections.get(source_path)
    except:
        raise iRODSExceptions.CollectionDoesNotExist

    try:
        os.chdir(target_path)
    except:
        raise NotADirectoryError
    iget(session, source_path)

def iputFile (session, root, root_dir, filename, user, zones):
                obj = session.data_objects.create(root_dir + "/" + filename, force=True)
                window_start = 0.0
                window_bytes = 0.0
                total_bytes = 0
                average_rate = 0.0
                check_interval = 1.0  # seconds
                dirpath = root + "/" + filename
                with obj.open('r+') as f_out:
                    # 2MiB chunks. Somewhat arbitrary, but pretty good in manual tests
                    chunk_size = 2 * 1024 * 1024
                    with open(dirpath, 'rb') as f_in:
                        window_start = time.time()
                        while True:
                            chunk = f_in.read(chunk_size)
                            if len(chunk) <= 0:
                                break
                            total_bytes += len(chunk)
                            window_bytes += len(chunk)
                            f_out.write(chunk)
                            curr_time = time.time()
#                            pdb.set_trace()

                            if curr_time >= window_start + check_interval:
#                                pdb.set_trace()
                                average_rate = 0.6 * average_rate + 0.4 * (window_bytes / (curr_time - window_start))
                                print('Total transferred: {} B ({}), Approximate Current Rate: {} B/s ({}/s)'.format(
                                    total_bytes, humanize.naturalsize(total_bytes, binary=True),
                                    int(average_rate), humanize.naturalsize(average_rate, binary=True)))
                                # reset window stats
                                window_start = time.time()
                                window_bytes = 0.0

                for zone in zones:
                    acl = iRODSAccess("own", root_dir + "/" + filename, user, zone)
                    session.permissions.set(acl)


def iput(session, source_path, target_path, user, zones):
#    pdb.set_trace()
    for root, subdirs, files in os.walk(source_path):

            temp_path = (root.split(os.path.dirname(source_path)))[1]
            root_dir = target_path + temp_path
            temp_root_dir = session.collections.create(root_dir)
            print(temp_root_dir.path)
            for subdir in subdirs:
                temp = session.collections.create(root_dir + "/" +  subdir)
                for zone in zones:
                    acl = iRODSAccess("own", root_dir + "/" + subdir, user, zone)
                    session.permissions.set(acl)

            for filename in files:
                iputFile (session, root, root_dir, filename, user, zones)

