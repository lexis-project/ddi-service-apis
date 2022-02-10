from shutil import copyfile, copytree, rmtree, move
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


def move_data(source_path, target_path):
    try:
        dirname = os.path.basename(source_path)
        full_target = target_path + "/" + dirname
        move(source_path, target_path)
        return full_target
    except BaseException:
        raise NotADirectoryError


def recursive_chmod(target_path):
    os.chmod(target_path, 0o700)
    for root, dirs, files in os.walk(target_path):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o700)
        for f in files:
            os.chmod(os.path.join(root, f), 0o700)
