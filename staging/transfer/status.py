import logging
import os
from transfer.models import DataTransfer
from celery.result import AsyncResult
from django.core.exceptions import ObjectDoesNotExist
from transfer import exceptions
from transfer import systems

logger = logging.getLogger(__name__)

def list_transfers(user):
    """
    Provides a list of selected columns from DataTransfer object

    Parameters
    ----------
    user - a valid Lexis DDI user

    Returns
    -------
    List of selected DataTransfer object fields, and Celery Task status for each request_id found
    """
    transfers = []
    for transfer in DataTransfer.objects.filter(user=user):
        celery_request = None
        if transfer.request_id is not None:
            celery_result = AsyncResult(transfer.request_id)
        transfers.append(get_transfer_dict(transfer))
    return transfers


def get_transfer_by_request(request_id):
    """
    Transfer is sucessful if the Celery task is in state SUCCESS

    Parameters
    ----------
    request_id - stored in the DB as field of the DataTransfer model

    Returns
    -------
    DataTransfer object
    """
    try:
        transfer = DataTransfer.objects.get(request_id=request_id)
        return transfer
       
    except ObjectDoesNotExist:
        raise exceptions.TransferNotFound


def get_transfer_dict(transfer):
     if transfer.request_id is not None:
            celery_result = AsyncResult(transfer.request_id)
     return {'request_id': transfer.request_id,
             'created_at': transfer.created_at,
             'project': transfer.project,
             'filename': transfer.filename,
             'task_state': celery_result.status,
             'task_result': str(celery_result.result),
             'transfer_type': transfer.transfer_type
            }


def get_staged_file_by_request(request_id):
    """
    Returns absolute path to the staged file or None if task was not successful and file does not exist

    Parameters
    ----------
    request_id - stored in the DB as field of the DataTransfer model

    Returns
    -------
    (DataTransfer object, path_to_staged_file)
    """

    transfer = get_transfer_by_request(request_id)

    if transfer.task_id is None or transfer.transfer_type != 'download':
        return None

    task_status = AsyncResult(transfer.task_id)
    if task_status.state == "SUCCESS" and os.path.isfile(task_status.result[1]):
        # The staging chain returns list [task_id, path_to_staged_file]
        return (transfer, task_status.result[1])

    if task_status.state == "FAILURE":
        raise exceptions.TransferError(str(task_status.result))

    return None
