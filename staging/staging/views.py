from . import errors
from . import trigger_task
from . import validate_input
from . import replication_api
from . import staging_api
from . import utils
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from celery.result import AsyncResult
from irods.connection import ExceptionOpenIDAuthUrl
import yaml

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)


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


def index(request):
    return HttpResponse("Welcome to the staging api")


@csrf_exempt
def stage(request):
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
            if dditoken is not None:
                data["token"] = dditoken
            if secrets is not None:
                data["secrets"] = secrets
            validate_input.validate_staging_input_body(data)
            staging = trigger_task.trigger_staging_task(data)
            if staging.status == "FAILURE":
                return errors.E403()
            task_id = staging.id
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except Exception as e:
            return errors.MalformedRequest(str(e))
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


@csrf_exempt
def check_status(request, req_id):
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
            result = "Transfer completed"
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
def delete_copy(request):
    try:
        if request.method == 'DELETE':
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
            validate_input.validate_deletion_input_body(data)
            delete = trigger_task.trigger_deletion_task(data)
            task_id = delete.id
            response_data = {'request_id': task_id}
            return HttpResponse(
                   json.dumps(response_data),
                   content_type="application/json",
                   status="201")
    except KeyError:
        return errors.MalformedRequest("Required parameters not provided")
    except json.decoder.JSONDecodeError:
        return errors.MalformedRequest("Invalid JSON")
    except AttributeError:
        return errors.NoAuth()
    except IndexError:
        return errors.NoAuth()


def check_deletion_status(request, req_id):
    res = AsyncResult(str(req_id))
    if str(res.state) == "PENDING":
        result = "Task still in the queue, or task does not exist"
    elif str(res.state) == "FAILURE":
        result = "Task Failed, reason: " + str(res.info)
    elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
        result = "Data deleted"
    else:
        result = "In progress"
    response_data = {'status': result}
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json",
        status="200")


def get_targets(request):
    target_systems = systems["systems"]
    targets = []
    for key in target_systems.keys():
        targets.append(key)
    return HttpResponse(
        json.dumps(targets),
        content_type="application/json",
        status="200")


@csrf_exempt
def replicate(request):
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
            validate_input.validate_replication_input_body(data)
            replication = trigger_task.trigger_replication(data)
            if replication.status == "FAILURE":
                return errors.E403()
            task_id = replication.id
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


def check_replication_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    data = None
    replication = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "Replication completed"
            data = res.get()
            replication = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if data is not None:
            response_data['PID'] = replication[1]
            response_data['target_path'] = replication[0]
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def assign_pid(request):
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
            validate_input.validate_pid_assignment_input_body(data)
            pid_assignment = trigger_task.trigger_pid_assignment(data)
            if pid_assignment.status == "FAILURE":
                return errors.E403()
            task_id = pid_assignment.id
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


def check_pid_assignment_status(request, req_id):
    if request.method != 'GET':
        return errors.E405()
    data = None
    pid = None
    try:
        res = AsyncResult(str(req_id))
        if str(res.state) == "PENDING":
            result = "Task still in the queue, or task does not exist"
        elif str(res.state) == "FAILURE":
            result = "Task Failed, reason: " + str(res.info)
        elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
            result = "PID assigned successfully"
            data = res.get()
            pid = data[1]
        else:
            result = "In progress"
        response_data = {'status': result}
        if data is not None:
            response_data['PID'] = pid
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status="200")
    except BaseException:
        return errors.MalformedRequest()


@csrf_exempt
def check_replication(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            response_data = {}
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = dditoken
            validate_input.validate_replication_status_input_body(data)
            status = replication_api.check_replication(data)
            utils.revokeToken(token)
            response_data['status'] = status
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="200")
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
def check_flags(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            response_data = {}
            token = request.headers.get('Authorization').split(" ")[1]
            (secrets, user, dditoken, refreshtoken,
             error) = utils.getDDIAttributes(token)
            if error is not None:
                check = 401
                return HttpResponse(
                    '{"status": "%s", "errorString": "%s"}' %
                    (check, error), content_type='application/json', status=check)
            data["token"] = dditoken
            validate_input.validate_replication_status_input_body(data)
            status = staging_api.get_enc_comp_flags(data)
            utils.revokeToken(token)
            response_data['encryption'] = status[0]
            response_data['compression'] = status[1]
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="200")
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
def get_size(request):
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
            validate_input.validate_data_size_input_body(data)
            size = trigger_task.trigger_get_data_size(data)
            if size.status == "FAILURE":
                return errors.E403()
            task_id = size.id
            response_data = {'request_id': task_id}
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json",
                status="201")
        except ExceptionOpenIDAuthUrl:
            return errors.AuthURL()
        except json.decoder.JSONDecodeError:
            return errors.MalformedRequest("Invalid JSON")
        except KeyError as ke:
            return errors.MalformedRequest(
                "Required parameter not found: {}".format(
                    ke.args[0]))
        except AttributeError:
            return errors.NoAuth()
        except IndexError:
            return errors.NoAuth()
    return errors.E405()


def check_size_status(request, req_id):
    size = None
    res = AsyncResult(str(req_id))
    if str(res.state) == "PENDING":
        result = "Task still in the queue, or task does not exist"
    elif str(res.state) == "FAILURE":
        result = "Task Failed, reason: " + str(res.info)
    elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
        result = "Done"
        data = res.get()
        size = data[1]
    else:
        result = "In progress"
    response_data = {'result': result}
    if size is not None:
        response_data['size'] = str(size[0])
        response_data['totalfiles'] = str(size[1])
        response_data['smallfiles'] = str(size[2])
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json",
        status="200")


@csrf_exempt
def duplicate(request):
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
            if dditoken is not None:
                data["token"] = dditoken
            if secrets is not None:
                data["secrets"] = secrets
            staging = trigger_task.trigger_duplication(data)
            if staging.status == "FAILURE":
                return errors.E403()
            task_id = staging.id
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
def check_duplication_status(request, req_id):
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
            result = "Duplication completed"
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
