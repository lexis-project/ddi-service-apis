from shutil import copyfile, copytree, rmtree
import os


def initiate_internal_nfs_to_transfer(source_path, target_path):
    try:
        if os.path.isdir(source_path):
            dirname = os.path.basename(source_path)
            full_target = target_path + "/" + dirname
            copytree(source_path, full_target)
            return full_target
        else:
            copyfile(source_path, target_path)
            filename = os.path.basename(source_path)
            return target_path + "/" + filename
    except BaseException:
        raise NotADirectoryError


def delete_nfs_target(target_path):
    try:
        if os.path.isdir(target_path):
            rmtree(target_path)
        else:
            os.remove(target_path)
            return target_path
    except BaseException:
        raise NotADirectoryError
