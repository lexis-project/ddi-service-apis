from transfer import tasks
from encryption import tasks as enc_tasks
from staging import tasks as staging_tasks
import os
import uuid
import logging
from celery import chain
from transfer import util
from transfer.systems import systems, get_burst_buffer_path, find_system_by_zone
import shutil
from transfer.models import DataTransfer
from staging import generate_config
import json

logger = logging.getLogger(__name__)

def trigger_tus_upload(data, secrets):
    logger.info("Finished TUS upload of {0}".format(data['filename']))
    # Get absolute path to the finished TUS uploaded file
    staging_area_path = systems['systems'][systems['burst_buffer_area']]['base_path']
    tus_file_path = os.path.join(staging_area_path, data['filename'])

    # Generate random directory
    tus_upload_directory = "tus_{0}".format(str(uuid.uuid1()))
    temp_directory = os.path.join(staging_area_path, tus_upload_directory)
    os.mkdir(temp_directory)

    # Move the TUS-uploaded file to the temp directory and rename it to its original name
    original_file_path = os.path.join(temp_directory, data['metadata']['filename'])
    shutil.move(tus_file_path, original_file_path)
    logger.info("File moved to: {0}".format(original_file_path))

    # Metadata in TUS are passed as JSON, parse and set
    metadata = json.loads(data['metadata']['metadata'])
   
    # Compose input data for staging tasks
    input_data = {
        'source_system': systems['burst_buffer_area'],
        'source_path': tus_upload_directory,
        'target_system': systems['local_irods'],
        'target_path': util.get_irods_path(data['metadata']['project'], data['metadata']['user'], data['metadata']['access']),
        'token': data['metadata']['token'],
        'metadata': metadata,
        'encryption': data['metadata']['encryption'],
        'compression': 'no',  # Not exposed in the API
        'secrets': secrets, 
        'project': data['metadata']['project']
    }

    source_location = generate_config.get_location(input_data["source_system"])
    target_location = generate_config.get_location(input_data["target_system"])
    staging_queue = generate_config.get_category(source_location, target_location)
    
    # Task chain contains these steps:
    # 1. Decompress (optional)
    # 2. Encrypt (optional)
    # 3. Stage to iRODS
    task_chain = []

    if data['metadata']['expand'] == 'yes':
        input_data['source_path'] = os.path.join(input_data['source_path'], data['metadata']['filename'])
        # Extract the incoming archive
        task_chain.append(enc_tasks.decompress.s(input_data).set(queue=systems['burst_buffer']))
        # Gotta glue it together
        task_chain.append(tasks.process_output_decompress.s(input_data).set(queue=staging_queue))

    if data['metadata']['encryption'] == 'yes':
        # Trigger encryption
        # If there is already expand task in the chain, do not pass input_data, it will be passed by the process_output_task
        if len(task_chain) > 0:
            task_chain.append(enc_tasks.encrypt.s().set(queue=systems['burst_buffer']))
        else:
            task_chain.append(enc_tasks.encrypt.s(input_data).set(queue=systems['burst_buffer']))
        
        # Gotta glue it together
        task_chain.append(tasks.process_output_encrypt.s(input_data).set(queue=staging_queue))

    # Trigger staging from local posix to iRODS
    task_chain.append(staging_tasks.stage_class_2.s(input_data).set(queue=staging_queue))

    result = chain(task_chain)()

    logger.info("Pushing file {0} to iRODS {1}".format(input_data['source_path'], input_data['target_path']))
    logger.info("Task ID: {0}".format(result.id))

    # Store the request in DB
    DataTransfer(
        project=data['metadata']['project'],
        user=data['metadata']['user'],
        access=data['metadata']['access'],
        zone=data['metadata']['zone'],
        filename=data['metadata']['filename'],
        transfer_type='upload',
        request_id=result.id).save()


def trigger_download_stage(data, token, user, secrets):
    # Generate random request identifier
    request_id = str(uuid.uuid1())

    # Create temp directory for this staging request
    target_directory = os.path.join(get_burst_buffer_path(), "download_{0}".format(request_id))
    os.mkdir(target_directory)

    # Build input data for staging task
    dataset_path = os.path.join(util.get_irods_path(data['project'], user, data['access']), data['dataset_id'])
    if not data['path'] or data['path'] != "/":
        dataset_path = os.path.join(dataset_path, data['path'])

    (source_system_name, source_system) = find_system_by_zone(data['zone'])

    input_data = {
        'source_system': source_system_name,
        'source_path': dataset_path,
        'target_system': systems['burst_buffer_area'],
        'target_path': "download_{0}".format(request_id),
        'token': token,
        'secrets': secrets,
        'project': data['project']
    }

    source_location = generate_config.get_location(input_data["source_system"])
    target_location = generate_config.get_location(input_data["target_system"])
    staging_queue = generate_config.get_category(source_location, target_location)

    # If dataset is encrypted add decryption task in the chain
    is_encrypted = util.get_dataset_encryption_flag(token, source_system_name, data['project'], data['access'], data['dataset_id'])

    task_chain = []

    # Trigger staging of this data
    task_chain.append(staging_tasks.stage_class_1.s(input_data).set(queue=staging_queue))
    # Gotta glue it together
    task_chain.append(tasks.process_output_staging.s(input_data).set(queue=staging_queue))

    # Decrypt dataset, if encrypted
    if is_encrypted:
        task_chain.append(enc_tasks.decrypt.s().set(queue=systems['burst_buffer']))
        task_chain.append(tasks.process_output_decrypt.s(input_data).set(queue=staging_queue))

    # Compress it
    task_chain.append(enc_tasks.compress.s().set(queue=systems['burst_buffer']))

    result = chain(task_chain)()

    # Save this request in DB
    DataTransfer(
        zone=source_system_name,
        project=data['project'],
        user=user,
        access=data['access'],
        filename=data['path'],
        request_id=request_id,
        task_id=result.id,
        transfer_type='download'
    ).save()

    return request_id