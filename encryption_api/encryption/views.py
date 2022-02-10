from django.shortcuts import render
from . import errors
from . import validate_input
from . import tasks
from . import utils
from celery import chain
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import requests
import json
import base64
import jwt
import jsonschema
import logging
from jsonschema import validate
from celery.result import AsyncResult
from celery import states
from irods.connection import ExceptionOpenIDAuthUrl
import sys
import yaml

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)


def get_queue():
    local_queue = systems["burst_buffer"]
    return local_queue


def index(request):
    return HttpResponse("Welcome to the encryption api")


def requestValidateToken(token):
    req = requests.get(
        systems["keycloak"]["microservice"] +
        '/validate_token',
        params={
            'provider': 'keycloak_openid',
            'access_token': token})
    if req.status_code == 200:
        j = req.json()
        if not j['active']:
            return 401
        return 200
    return req.status_code


@csrf_exempt
def encrypt(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = dditoken
            data["secrets"] = secrets
            validate_input.validate_encryption_input_body(data)
            local_queue = get_queue()
            cel_task = tasks.encrypt.s(data).set(queue=local_queue)
            encryption = cel_task.apply_async()
            if encryption.status == "FAILURE":
                return errors.E403()
            task_id = str(encryption.id)
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError:
            return errors.MalformedRequest("Required parameter not found")
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def encryption_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    target_path = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Encryption completed"
            data = res.get()
            target_path = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if target_path is not None:
            response_data['target_path'] = target_path
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def decrypt(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = dditoken
            data["secrets"] = secrets
            validate_input.validate_encryption_input_body(data)
            local_queue = get_queue()
            cel_task = tasks.decrypt.s(data).set(queue=local_queue)
            decryption = cel_task.apply_async()
            if decryption.status == "FAILURE":
                return errors.E403()
            task_id = str(decryption.id)
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError:
            return errors.MalformedRequest("Required parameter not found")
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def decryption_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    target_path = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Decryption completed"
            data = res.get()
            target_path = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if target_path is not None:
            response_data['target_path'] = target_path
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def compress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = token
            validate_input.validate_encryption_input_body(data)
            local_queue = get_queue()
            cel_task = tasks.compress.s(data).set(queue=local_queue)
            compression = cel_task.apply_async()
            if compression.status == "FAILURE":
                return errors.E403()
            task_id = str(compression.id)
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError:
            return errors.MalformedRequest("Required parameter not found")
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def compression_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    target_path = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Compression completed"
            data = res.get()
            target_path = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if target_path is not None:
            response_data['target_path'] = target_path
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def decompress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = token
            validate_input.validate_encryption_input_body(data)
            local_queue = get_queue()
            cel_task = tasks.decompress.s(data).set(queue=local_queue)
            decompression = cel_task.apply_async()
            if decompression.status == "FAILURE":
                return errors.E403()
            task_id = str(decompression.id)
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError:
            return errors.MalformedRequest("Required parameter not found")
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def decompression_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    target_path = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Decompression completed"
            data = res.get()
            target_path = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if target_path is not None:
            response_data['target_path'] = target_path
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def compress_encrypt(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = dditoken
            data["secrets"] = secrets
            validate_input.validate_encryption_input_body(data)
            local_queue = get_queue()
            cel_task = tasks.compress_encrypt.s(data).set(queue=local_queue)
            encryption = cel_task.apply_async()
            if encryption.status == "FAILURE":
                return errors.E403()
            task_id = str(encryption.id)
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError:
            return errors.MalformedRequest("Required parameter not found")
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def compression_encryption_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    target_path = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Compression and Encryption completed"
            data = res.get()
            target_path = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if target_path is not None:
            response_data['target_path'] = target_path
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def decrypt_decompress(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = dditoken
            data["secrets"] = secrets
            data["token"] = token
            validate_input.validate_encryption_input_body(data)
            local_queue = get_queue()
            cel_task = tasks.decrypt_decompress.s(data).set(queue=local_queue)
            decryption = cel_task.apply_async()
            if decryption.status == "FAILURE":
                return errors.E403()
            task_id = str(decryption.id)
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError:
            return errors.MalformedRequest("Required parameter not found")
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def decryption_decompression_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    target_path = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Decryption and Decompression completed"
            data = res.get()
            target_path = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if target_path is not None:
            response_data['target_path'] = target_path
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()
