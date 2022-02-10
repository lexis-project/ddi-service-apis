import secrets
import uuid
from transfer import auth
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, FileResponse
from transfer import util
from transfer import validate_input
from transfer import trigger_tasks
import json
import yaml
from celery.result import AsyncResult
from django_tus.views import TusUpload
from django.views.decorators.csrf import csrf_exempt
from django.dispatch import receiver
from django_tus.signals import tus_upload_finished_signal
from django_tus.response import TusResponse
from transfer import status
from transfer import exceptions
import logging

logger = logging.getLogger(__name__)


class ErrorResponse(JsonResponse):
    def __init__(self, message, code, **kwargs):
        data = {"status": code, "errorString": message}
        super().__init__(data=data, status=code, **kwargs)

@csrf_exempt
@require_POST
def stage_download(request):
    
    try:
        (token, user) = auth.authentize_request(request)
    except exceptions.TransferError:
        return ErrorResponse("Authentinzation error.", 500)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Invalid token", 401)
    

    try:
        data = json.loads(request.body.decode('utf-8'))
      
        # Validate download request
        validate_input.download(data)

        # Exchange token
        dditoken = auth.exchange_token(token)

        # Authorize
        auth.authorize_request(dditoken, data['project'], 'dat_read')

        # Get secrects
        secrets = auth.get_secrets(token)

        # Trigger downloading
        request_id = trigger_tasks.trigger_download_stage(data, dditoken, user, secrets)
        return JsonResponse({"requestId": request_id}, status=200)

    except json.JSONDecodeError as je:
        logger.error("Cannot decode download request body: {0}".format(je))
        return ErrorResponse("Cannot decode JSON body: {0}".format(je), 400)
    except exceptions.TransferInvalidParameter as te:
        return ErrorResponse(str(te), 400)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Permission denied", 403)
    except exceptions.TransferError:
        return ErrorResponse("Internal error.", 500)   


@csrf_exempt
@require_GET
def download_staged(request, request_id):
    try:
        (token, user) = auth.authentize_request(request)
    except exceptions.TransferError:
        return ErrorResponse("Authentinzation error.", 500)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Invalid token", 401)

    # Try to get staged file path
    try:
        # Exchange token
        dditoken = auth.exchange_token(token)

        (transfer_request, staged_file) = status.get_staged_file_by_request(request_id)

        # Authorize
        auth.authorize_request(dditoken, transfer_request.project, 'dat_read')


    except exceptions.TransferError as te:
        return ErrorResponse("Transfer failed: {0}".format(te), 400)
    except exceptions.TransferNotFound:
        return ErrorResponse("Transfer not found: {0}".format(request_id), 404)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Unauthorized", 403)

    if staged_file:
        return FileResponse(open(staged_file, 'rb'))
    else:
        return ErrorResponse("Staged not found: {0}".format(request_id), 404)


@csrf_exempt
def list_transfers(request):
    try:
        (token, user) = auth.authentize_request(request)
    except exceptions.TransferError:
        return ErrorResponse("Authentinzation error.", 500)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Invalid token", 401)

    return JsonResponse(data=status.list_transfers(user), safe=False)

@csrf_exempt
def get_transfer(request, req_id):
    try:
        (token, user) = auth.authentize_request(request)
    except exceptions.TransferError:
        return ErrorResponse("Authentinzation error.", 500)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Invalid token", 401)

    transfer = status.get_transfer_by_request(req_id)
    if transfer:
        return JsonResponse(data=status.get_transfer_dict(transfer), safe=False)
    else:
        return ErrorResponse("Not found", 404)


@csrf_exempt
def tus_upload(*args, **kwargs):
    request = args[0]
    try:
        (token, user) = auth.authentize_request(request)
    except exceptions.TransferError:
        return ErrorResponse("Authentinzation error.", 500)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Invalid token", 401)


    # Append token and user keys
    args[0].META['HTTP_UPLOAD_METADATA'] = util.append_tus_meta(args[0].META['HTTP_UPLOAD_METADATA'], 'token', token)
    args[0].META['HTTP_UPLOAD_METADATA'] = util.append_tus_meta(args[0].META['HTTP_UPLOAD_METADATA'], 'user', user)

    # Validate metadata
    try:
        meta = util.get_metadata(request)
        validate_input.upload(meta)

        # Authorize
        auth.authorize_request(token, meta['project'], 'dat_write')

    except exceptions.TransferInvalidParameter as te:
        logger.error(te)
        return TusResponse(status=400, content="Invalid TUS metadata.")
   
    return TusUpload.as_view()(*args, **kwargs)


@receiver(tus_upload_finished_signal)
def tus_upload_finished(sender, **kwargs):
    try:
        (token, user) = auth.authentize_request(None, kwargs['metadata']['token'])
    except exceptions.TransferError:
        return ErrorResponse("Authentinzation error.", 500)
    except exceptions.TransferUnauthorized:
        return ErrorResponse("Invalid token", 401)

    # Exchange token
    dditoken = auth.exchange_token(token)

    # Authorize
    auth.authorize_request(dditoken, kwargs['metadata']['project'], 'dat_write')

    # Get secrects
    secrets = auth.get_secrets(token)

    # Exchange original access token for offline token for DDI which is validated on iRODS broker
    kwargs['metadata']['token'] = dditoken

    # Trigger task for staging to iRODS
    trigger_tasks.trigger_tus_upload(kwargs, secrets)