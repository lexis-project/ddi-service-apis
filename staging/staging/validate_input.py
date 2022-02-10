from . import generate_config
from . import verifyMetadata
import logging
import yaml

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)


def validate_staging_input_body(input_data):
    try:
        logging.info(input_data["source_system"])
        logging.info(input_data["target_system"])
        logging.info(input_data["source_path"])
        logging.info(input_data["target_path"])
        logging.info(input_data["encryption"])
        logging.info(input_data["compression"])
        source_system = input_data["source_system"]
        target_system = input_data["target_system"]
        source_type = generate_config.get_type(source_system)
        target_type = generate_config.get_type(target_system)

    except KeyError:
        raise KeyError(
            "Input is not valid. Please check source and target information")
    # Encryption and compression flags validation
    if "encryption" not in input_data or "compression" not in input_data:
        raise KeyError(
            "Input is not valid. Check encryption and compression values")
    if input_data["encryption"] != "yes" and input_data["encryption"] != "no":
        raise KeyError(
            "Input is not valid. Check encryption values. Allowed values are yes or no")
    if input_data["compression"] != "yes" and input_data["compression"] != "no":
        raise KeyError(
            "Input is not valid. Check compression values. Allowed values are yes or no")
    if source_type == "HPC" or target_type == "HPC":
        try:
            logging.info(input_data["task_id"])
            logging.info(input_data["job_id"])
            logging.info(input_data["heappe_url"])
        except KeyError:
            raise KeyError(
                "Input is not valid. HEAppE job and task id are required")
    elif target_type == "iRODS":
        try:
            logging.info(input_data["metadata"])
            e = verifyMetadata.verifyMetadataForUpload(input_data["metadata"])
            if e is not None:
                raise Exception("Metadata is not valid: " + e)
        except KeyError:
            raise KeyError("Input is not valid. Metadata are required")
    try:
        logging.info(systems["systems"][source_system])
        logging.info(systems["systems"][target_system])
    except KeyError:
        raise (KeyError("Source or target doesn't exist!"))


def validate_deletion_input_body(input_data):
    try:
        logging.info(input_data["target_system"])
        logging.info(input_data["target_path"])
        target_system = input_data["target_system"]
        target_type = generate_config.get_type(target_system)
    except KeyError:
        raise KeyError("Input is not valid. Please check target information")
    if target_type == "HPC":
        try:
            logging.info(input_data["task_id"])
            logging.info(input_data["job_id"])
            logging.info(input_data["heappe_url"])
        except KeyError:
            raise KeyError(
                "Input is not valid. HEAppE job and task id are required")
    try:
        logging.info(systems["systems"][target_system])
    except KeyError:
        raise KeyError("Target doesn't exist!")


def validate_replication_input_body(input_data):
    try:
        logging.info(input_data["source_system"])
        logging.info(input_data["source_path"])
        logging.info(input_data["target_system"])
        source_system = input_data["source_system"]
        target_system = input_data["target_system"]
    except KeyError:
        raise KeyError(
            "Input is not valid. Please check source or target information")
    try:
        logging.info(systems["systems"][source_system])
        logging.info(systems["systems"][target_system])
    except KeyError:
        raise (Exception("Source or Target doesn't exist!"))


def validate_pid_assignment_input_body(input_data):
    try:
        logging.info(input_data["source_system"])
        logging.info(input_data["source_path"])
        source_system = input_data["source_system"]
    except KeyError:
        raise KeyError("Input is not valid. Please check target information")
    try:
        logging.info(systems["systems"][source_system])
    except KeyError:
        raise (Exception("Source doesn't exist!"))


def validate_replication_status_input_body(input_data):
    try:
        logging.info(input_data["target_system"])
        logging.info(input_data["target_path"])
        target_system = input_data["target_system"]
    except KeyError:
        raise KeyError("Input is not valid. Please check target information")
    try:
        logging.info(systems["systems"][target_system])
    except KeyError:
        raise (Exception("Target doesn't exist!"))


def validate_data_size_input_body(input_data):
    try:
        logging.info(input_data["target_system"])
        logging.info(input_data["target_path"])
        target_system = input_data["target_system"]
    except KeyError:
        raise KeyError("Input is not valid. Please check target information")
    try:
        logging.info(systems["systems"][target_system])
    except KeyError:
        raise KeyError("Target doesn't exist!")
