import logging
import base64
import binascii
import os
import shutil
from staging_api.celery import app
import yaml
from transfer.systems import systems

logger = logging.getLogger(__name__)


@app.task(bind=True)
def store_file(self, input_data):
    """
    Stores base64 encode file in input_data['data'] on local storage
    Parameters
    ----------
    self
    input_data - Staging request with source_system, source path and data keys (must correspond to systems.yml)

    Returns
    -------
    Original input data without the 'data' field

    """
    absolute_path = os.path.join(systems['systems'][input_data['source_system']]['base_path'], input_data['source_path'])
    logging.info("Storing file at: {0}".format(absolute_path))
    try:
        os.mkdir(os.path.split(absolute_path)[0])
        with open(absolute_path, 'wb') as f:
            f.write(base64.b64decode(input_data['data'].replace("\n", ""), validate=True))
            del input_data['data']
    except OSError as e:
        logging.error("Unable to store uploaded file: {0} - {1}".format(absolute_path, e))
    except binascii.Error:
        logging.error("Invalid base64 encoded data")
    return input_data


@app.task(bind=True)
def process_output_staging(self, staging_output, input_data):
    """

    Parameters
    ----------
    self
    staging_output - Output of stage X staging tasks [task_id, data]
    input_data - Rest of the input data used for this staging chain

    Returns
    -------
    Input data for correct format for the compress task
    """
    logger.info("Got staging task output: {0}".format(staging_output))

    input_data['source_system'] = input_data['target_system']
    input_data['source_path'] = input_data['target_path']

    return input_data


@app.task(bind=True)
def process_output_encrypt(self, encrypt_output, input_data):
    """

    Parameters
    ----------
    self
    staging_output - Output of stage X staging tasks [task_id, data]
    input_data - Rest of the input data used for this staging chain

    Returns
    -------
    Input data for correct format for the compress task
    """
    logger.info("Got encryption task output: {0}".format(encrypt_output))

    # Compose input data for encryption task
    # Remove the part leading to the bb area
    encrypted_path_no_prefix = encrypt_output[1][len(systems['systems'][input_data['source_system']]['base_path']):]
    input_data['source_path'] = encrypted_path_no_prefix
    return input_data

@app.task(bind=True)
def process_output_decrypt(self, decrypt_output, input_data):
    """

    Parameters
    ----------
    self
    staging_output - Output of stage X staging tasks [task_id, data]
    input_data - Rest of the input data used for this staging chain

    Returns
    -------
    Input data for correct format for the compress task
    """
    logger.info("Got decryption task output: {0}".format(decrypt_output))

    # Compose input data for encryption task
    # Remove the part leading to the bb area
    decrypted_path_no_prefix = decrypt_output[1][len(systems['systems'][input_data['target_system']]['base_path']):]
    input_data['source_path'] = decrypted_path_no_prefix
    input_data['source_system'] = input_data['target_system']
    input_data['target_path'] = ""
    return input_data


@app.task(bind=True)
def process_output_decompress(self, decompress_output, input_data):
    """

    Parameters
    ----------
    self
    staging_output - Output of stage X staging tasks [task_id, data]
    input_data - Rest of the input data used for this staging chain

    Returns
    -------
    Input data for correct format for the compress task
    """
    logger.info("Got decompress task output: {0}".format(decompress_output))

    # Compose input data for the following tash
    # Remove the bb path prefix from the task output
    decrypted_path_no_prefix = decompress_output[1][len(systems['systems'][input_data['source_system']]['base_path']):]
    input_data['source_path'] = decrypted_path_no_prefix
    return input_data