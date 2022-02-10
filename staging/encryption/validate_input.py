import logging
import yaml

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)


def validate_encryption_input_body(input_data):
    try:
        logging.info(input_data["source_system"])
        logging.info(input_data["source_path"])
        source_system = input_data["source_system"]
    except KeyError:
        raise Exception(
            "Input is not valid. Please check source and target information")
    try:
        logging.info(systems["systems"][source_system])
    except KeyError:
        raise (Exception("Source or target doesn't exist!"))


def validate_decryption_input_body(input_data):
    try:
        logging.info(input_data["source_system"])
        logging.info(input_data["source_path"])
        source_system = input_data["source_system"]
    except KeyError:
        raise Exception(
            "Input is not valid. Please check source and target information")
    try:
        logging.info(systems["systems"][source_system])
    except KeyError:
        raise (Exception("Source or target doesn't exist!"))
