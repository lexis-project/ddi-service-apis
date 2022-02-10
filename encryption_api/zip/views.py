from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from celery.result import AsyncResult
import json
import yaml
import logging
import requests
from encryption import utils
from encryption.errors import (NoAuth, E403, E405, MalformedRequest)
from encryption.tasks import decrypt, decompress, decrypt_decompress
from irods.connection import ExceptionOpenIDAuthUrl
from . import tasks

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)

def requestValidateToken(token):
    req= requests.get (systems["keycloak"]["microservice"]+'/validate_token',
             params = {'provider': 'keycloak_openid', 'access_token': token})
    if req.status_code == 200:
       j=req.json()
       if j['active']==False:
           return 401
       return 200
    return req.status_code

@csrf_exempt
def zip(request):
    if request.method != 'POST':
        return E405()

    try:
       #pdb.set_trace()
       data = json.loads(request.body.decode('utf-8'))
       source_system = data['source_system']
       source_path = data['source_path']
       size = data['size']
       token=request.headers.get('Authorization').split(" ")[1]
       cleanup=data.get('delete_source', False)
       check=requestValidateToken(token)
       if (check != 200):
          message = "Unable to connect to keycloak service"
          if check == 401:
            message = "Unauthorized"
          return HttpResponse('{"status": "%s", "errorString": "%s"}'%(check, message),
              content_type='application/json', status=check)
       if source_system != systems["burst_buffer_area"]:
          return MalformedRequest("Invalid source_system")
      # res =  tasks.zip.delay(source_system, source_path, token, size)
       bb_queue = systems["burst_buffer"]
       zip_process = tasks.zip.s(source_system, source_path, token, size, cleanup).set(queue=bb_queue)
       res = zip_process.apply_async()
       logging.info(res.backend)
       if (res.status=="FAILURE"):
           return E403()
       id = str(res)
       response_data = {'request_id': id}
       return HttpResponse(json.dumps(response_data), content_type="application/json", status = "201")
       # staging_api.initiate_transfer(source_system, source_path, target_system, target_path, token)
    except ExceptionOpenIDAuthUrl:
        return AuthURL()
    except json.decoder.JSONDecodeError:
        return MalformedRequest("Invalid JSON")
    except KeyError:
        return MalformedRequest("Required parameter not found")
    except AttributeError:
        return NoAuth()
    except IndexError:
        return NoAuth()

@csrf_exempt
def check_status(request,req_id):
  if request.method != 'GET':
       return E405()
  target_paths = None
  password = None
  try:
    res = AsyncResult(str(req_id))
    result = "Started"
    if str(res.state)=="PENDING":
        result="Task still in the queue, or task does not exist"
    elif str(res.state)=="FAILURE":
        result= "Task Failed, reason: "+str(res.info)
    elif str(res.ready()) == "True" and str(res.state) == "SUCCESS":
       result= "Multipart zip created!"
       data = res.get()
       target_paths=data[1]
       password=data[2]
    else:
        result= "In progress: "+res.info["custom"]
    response_data = {}
    response_data['status'] = result
    if target_paths is not None:
        response_data['target_paths'] = target_paths
    if password is not None:
        response_data['password'] = password
    return HttpResponse(json.dumps(response_data), content_type="application/json", status = "200")
  except Exception as e:
    return MalformedRequest(str(e))
  return HttpResponse(str(res.ready()))

