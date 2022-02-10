import yaml

with open("/etc/staging_api/system.yml") as file:
    input_data = yaml.load(file, Loader=yaml.FullLoader)
    systems = input_data["systems"]
    local = input_data["local"]
    bb_queue = input_data["burst_buffer"]


def get_class(source_type, source_location, target_type, target_location):
    if (source_location ==
            target_location) or source_location == "federation" or target_location == "federation":
        if source_type == "iRODS" and (
                target_type == "NFS" or target_type == "SSFS"):
            return 1
        elif (source_type == "NFS" or source_type == "SSFS") and target_type == "iRODS":
            return 2
        elif (source_type == "NFS" or source_type == "SSFS") and (target_type == "NFS" or target_type == "SSFS"):
            return 3
        elif source_type == "iRODS" and target_type == "HPC":
            return 4
        elif source_type == "HPC" and target_type == "iRODS":
            return 5
        elif (source_type == "NFS" or source_type == "SSFS") and target_type == "HPC":
            return 6
        elif source_type == "HPC" and (target_type == "NFS" or target_type == "SSFS"):
            return 7
        else:
            return -1
    elif source_location != target_location:
        if (source_type == "NFS" or source_type ==
                "SSFS") and target_type == "HPC":
            return 8
        elif source_type == "HPC" and (target_type == "NFS" or target_type == "SSFS"):
            return 9
        elif (source_type == "NFS" or source_type == "SSFS") and (target_type == "NFS" or target_type == "SSFS"):
            return 10
        else:
            return -1
    else:
        return -1


def get_category(source_location, target_location):
    if source_location == local:
        return local
    elif source_location != local and source_location != "federation":
        return source_location
    elif source_location == "federation" and target_location == local:
        return local
    elif source_location == "federation" and target_location != local:
        return target_location
    else:
        return "Z"


def get_location(system_name):
    system_location = systems[system_name]["location"]
    return system_location


def get_type(system_name):
    system_type = systems[system_name]["type"]
    return system_type


def get_deletion_class(target_type):
    if target_type == "iRODS":
        return "del_1"
    elif target_type == "NFS" or target_type == "SSFS":
        return "del_2"
    elif target_type == "HPC":
        return "del_3"
    else:
        return -1


def get_local_queue():
    return local


def get_bb_queue():
    return bb_queue


def get_bb_area():
    return input["burst_buffer_area"]
