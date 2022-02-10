import base64
import binascii
import json
import logging
import os.path
import re
import shutil
import struct
import time
from zipfile import ZipFile
import jsonschema
import requests
import uuid
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.exceptions import RequestDataTooBig
from django.http import FileResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.utils import ProgrammingError
from django_tus.tusfile import TusFile

from .settings import IRODS, GLOBUS, STAGING

from irods.manager.collection_manager import CollectionManager
from irods.exception import (CollectionDoesNotExist, CAT_NO_ACCESS_PERMISSION, CAT_NO_ROWS_FOUND,
                             UserGroupDoesNotExist, NetworkException, SYS_INTERNAL_NULL_INPUT_ERR,
                             SYS_INVALID_INPUT_PARAM, CAT_UNKNOWN_COLLECTION, CAT_SQL_ERR)
from irods.models import DataObject, DataObjectMeta, Collection, CollectionMeta

from irods.connection import ExceptionOpenIDAuthUrl
from irods.exception import (CollectionDoesNotExist, CAT_NO_ACCESS_PERMISSION, CAT_NO_ROWS_FOUND,
                             UserGroupDoesNotExist, NetworkException, SYS_INVALID_INPUT_PARAM, SYS_INTERNAL_NULL_INPUT_ERR, iRODSException)
from irodsApisForWp8 import group, irods_transfer
from jsonschema import validate

from .metadata import (checkCustom)
from .models import UploadedFile
from .settings import IRODS, STAGING
from .utils import (GetUserAndTokenAPI, AuthURL,
                    MalformedRequest, E403, E405, E501, getIrodsPathNoZone, getIrodsPath, GetSession,
                    getListableProjects, getReadableProjects, getWritableProjects, revokeToken)

from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Create your views here.

metadataSingleValue=  ['identifier', 'title', 'publicationYear', 'resourceType', 'resourceTypeGeneral', 'CustomMetadata', 
                       'scope', 'format']
metadataMultiValue= ['creator', 'publisher', 'owner', 'contributor', 'relatedIdentifier',
              'rights', 'rightsURI', 'rightsIdentifier', 'CustomMetadataSchema', 'AlternateIdentifier', 'RelatedSoftware',
              'description']
#Each alternate identifier  has a sub-property AlternateIdentifierType, concatenate using json.encode
#'CustomMetadata', ''CustomMetadataSchema' are special because they need to be json-stringified.
metadataEUDAT=['EUDAT/FIO', 'EUDAT/FIXED_CONTENT', 'EUDAT/PARENT', 'EUDAT/ROR', 'PID', 'EUDAT/REPLICA']
metadataEncComp=['encryption', 'compression']

def datasetMeta(d, metadata):
    for x in metadataSingleValue:
        try:
           d[x]=metadata.get_one(x).value
           if x == 'CustomMetadata' :
              d[x]=json.loads(d[x])
        except:
           pass
#           print('Irods metadata for ' + x + ' does not conform to standard, ignoring')
    for x in metadataMultiValue:
           d[x]=[]
           if  x == 'CustomMetadataSchema' or x == 'AlternateIdentifier':
               for y in metadata.get_all(x):
                    j = json.loads(y.value)
                    if x == 'AlternateIdentifier' and isinstance(j, str):
                        # double json-encodeing
                        d[x].append (json.loads(j))
                    else:
                        d[x].append (j)
           else:
               for y in metadata.get_all(x):
                  d[x].append (y.value)

def datasetEudat(d, metadata):
    for x in metadataEUDAT:
        try:
           d[x]=metadata.get_one(x).value
        except:
           pass
#           print('Irods metadata for ' + x + ' does not conform to standard, ignoring')

def datasetEncComp(d, metadata):
    for x in metadataEncComp:
        try:
           d[x]=metadata.get_one(x).value
        except:
           pass

def DatasetCheckPermission(session, access, user, project, token, attr):
    writableprojects=getWritableProjects(attr)
    if not project in writableprojects:
       return E403()
    try:
          if access=='public':
              res=group.check_adm_user_project_membership(session, user, project)
          elif access=='project' or access == 'user':
              res=group.check_user_project_membership(session, user, project)
          else:
              return MalformedRequest("Access not user, project or public")
          if res==False:
              return E403()
    except UserGroupDoesNotExist:
        return E403()
    return None

@csrf_exempt
def DatasetCheckPermissionAPI(request):
  (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
  if err is not None:
     return err
  if request.content_type!='application/json' and request.content_type!='text/json':
     revokeToken(dditoken)
     return MalformedRequest("Content-type should be applicaton/json")
  with GetSession (dditoken, user) as session:
    try:
        q=json.loads(request.body.decode('utf-8'))
        access=q['access']
        project=q['project']
        err= DatasetCheckPermission(session, access, user, project, dditoken, attr)
        session.cleanup()
        revokeToken(dditoken)
        if (err):
           return err
        return HttpResponse ('{"status": "200"}', content_type='application/json')
    except json.decoder.JSONDecodeError:
        session.cleanup()
        revokeToken(dditoken)
        return MalformedRequest("Invalid JSON")
    except KeyError:
        session.cleanup()
        revokeToken(dditoken)
        return MalformedRequest("Required field missing")

@csrf_exempt
def deleteDatasetAPI(request):
  (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
  if err is not None:
     return err
  if request.content_type!='application/json' and request.content_type!='text/json':
     return MalformedRequest("Content-type should be applicaton/json")
  with GetSession (dditoken, user) as session:
    try:
        q=json.loads(request.body.decode('utf-8'))
        name=q['internalID']
        access=q['access']
        project=q['project']
        subpath=q.get('path', None)
        writableprojects=getWritableProjects(attr)
        if not project in writableprojects:
           session.cleanup()
           revokeToken(dditoken)
           return E403()
        err=DatasetCheckPermission(session, access, user, project, token, attr)
        if err is not None:
           session.cleanup()
           revokeToken(dditoken)
           return err
        irodsroute=getIrodsPathNoZone(access, user, project)+'/'+name
        if subpath is not None:
           irodsroute=irodsroute+'/'+subpath
#        session.collections.remove(irodsroute)
#use staging instead.
        url=STAGING["service"]+'/delete'
        req=requests.delete(url, 
                            headers={"Authorization": "Basic "+token, 
                                     "Content-Type": "application/json"}, 
                            verify=STAGING["sslVerification"], 
                            json={
                 "target_system" : STAGING["source_system"],
                 "target_path": irodsroute})
        if req.status_code != 201  :
                session.cleanup()
                revokeToken(dditoken)
                return HttpResponse ('{"errorString": "Error connecting to staging backend post: '+
                        '(error: %s, additional: %s)"}'%(req.status_code, json.dumps(req.text)[1:-1]),
                                     content_type='application/json', status=503)
        request_id=req.json()["request_id"]
        session.cleanup()
        revokeToken(dditoken)
        return HttpResponse ('{"errorString": "Request queued on staging api", "stagingAPI": "%s", "request_id": "%s"}'%(url, request_id), content_type='application/json', status=201)
    except CAT_NO_ROWS_FOUND:
        session.cleanup()
        revokeToken(dditoken)
        return HttpResponse (status=204)
    except json.decoder.JSONDecodeError:
        session.cleanup()
        revokeToken(dditoken)
        return MalformedRequest("Invalid JSON")
    except KeyError:
        session.cleanup()
        revokeToken(dditoken)
        return MalformedRequest("Required field missing")
#    return HttpResponse ('{"status": "500", "errorString": "Server failure"}',
#             content_type='application/json', status=405), 
          # Should never happen.

#https://stackoverflow.com/questions/4313508/execute-code-in-django-after-response-has-been-sent-to-the-client
class FileResponseCleanup(FileResponse):
    def __init__(self, data, CleanupFiles, **kwargs):
        super().__init__(data, **kwargs)
        self.CleanupFiles = CleanupFiles

    def __del__(self):
        #https://stackoverflow.com/questions/36722390/python-3-super-del
        getattr(super(), "__del__", lambda self: None)(self)
        shutil.rmtree(self.CleanupFiles)
#rgh: does not work on FileResponse as it is not a derived class
#investigate other methods for cleanup

def callStaging_Enc(url, endpoint, token, json_body, localpath):
    req=requests.post(url + "/" + endpoint, headers={"Authorization": "Basic "+token, "Content-Type": "application/json"}, verify=STAGING["sslVerification"], json=json_body)
    if req.status_code != 201:
      shutil.rmtree(localpath)
      return None, HttpResponse ('{"errorString": "Error connecting to staging backend post: '+
                                 '(error: %s, additional: %s)"}'%(req.status_code, req.content),
                                 content_type='application/json', status=503)
    request_id=req.json()["request_id"]
    print ("request id = "+request_id)
          #return req_id here later
    loops=0
    correct_response = ["Transfer completed", "Compression completed", "Decompression completed", "Compression and Encryption completed", "Decompression and Decompression completed", "Encryption completed", "Decryption completed"]
    while True:
      time.sleep(1)
      status_endpoint = url + "/" + endpoint + "/" + request_id
      req=requests.get(status_endpoint, headers={"Authorization": "Basic "+token},
                       verify=STAGING["sslVerification"])
      if req.status_code != 200:
        shutil.rmtree(localpath)
        return None, HttpResponse ('{"errorString": "Error connecting to staging backend get: (%s)"}'%
                     req.status_code, content_type='application/json', status=503)

      resp=req.json()["status"]
      if (resp == "Task Failed, reason: Irods path does not exist" or resp == "Task Failed, reason: Permission Denied" or
         resp == "Task Failed, reason: Dataset doesn't exist or wrong target path" ):
          shutil.rmtree(localpath)
          return None, HttpResponse ('{"errorString": "Dataset does not exist or insufficient permissions"}',
                                    content_type='application/json', status=403)
      if not resp in correct_response and resp != "Task still in the queue, or task does not exist" and resp != "In progress":
          shutil.rmtree(localpath)
          return None, HttpResponse('{"errorString": "Staging backend returned (%s)"}'%str(resp),
                                   content_type='application/json', status=503)
      loops+=1
      if (loops > 100):
          shutil.rmtree(localpath)
          return None, HttpResponse ('{"status": "503", "errorString": "Transfer took too long, cancelling"}', 
                             content_type='application/json', status=503)
      if resp == "Task still in the queue, or task does not exist" or resp == "In progress":
         continue
      return req, None

@csrf_exempt
def downloadDatasetAPI(request):
    (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
    if err is not None:
        return err
    try:
          q=json.loads(request.body.decode('utf-8'))
          name=q['internalID']
          access=q['access']
          project=q['project']
          zone = q.get('zone', IRODS['zone'])
          readableprojects=getReadableProjects(attr)
          if access != "public" and not project in readableprojects:
             revokeToken(dditoken)
             return E403()
          method=q.get('push_method', "directupload")
          if method != "directupload":
             revokeToken(dditoken)
             return E501()
          archivetype=q.get('compressmethod', "zip")
          if archivetype != "zip":
             revokeToken(dditoken)
             return E501()
          subpath = q.get('path', "")
          (localpath, err) = downloadDatasetInternal(request, dditoken, name, access, user, project, zone, method, archivetype, subpath)
          revokeToken(dditoken)
          if err is not None:
              return err
          return FileResponseCleanup(open(localpath+"/dataset.zip", 'rb'), CleanupFiles=localpath)
    except KeyError:
          revokeToken(dditoken)
          return MalformedRequest("Required Field missing")
    except json.decoder.JSONDecodeError:
          revokeToken(dditoken)
          return MalformedRequest("Invalid json")

def downloadDatasetInternal(request, token, name, access, user, project, zone, method, archivetype, subpath, multipart=None):
    try:
          basepath=str(uuid.uuid1())
          print("Base path is: " + basepath)
          localpath=STAGING['path']+'/'+basepath
          os.mkdir(localpath)
#different APIs may run as different users, and they need to be able to write here
          os.chmod(localpath, 0o777)
          print( "Local path is: " + localpath)
          irodspath=getIrodsPathNoZone(access, user, project)
          if subpath=="":
             irodsroute=irodspath+'/'+name
          else:
             irodsroute=irodspath+'/'+name+'/'+subpath
          print("iRODS path is: " + irodsroute)
          fullirodspath = irodspath=getIrodsPath(access, user, project, zone)
          if subpath=="":
             fullirodsroute=fullirodspath+'/'+name
          else:
             fullirodsroute=fullirodspath+'/'+name+'/'+subpath
          (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
          if err is not None:
            return err
          session = GetSession (dditoken, user)
          flags = get_encryption_compression_meta( session, fullirodspath+'/'+name)
          if flags [2] != None:
              session.cleanup()
              return None,  HttpResponse('{"status": "403", "errorString": "Dataset does not exist"}',
                                                                   content_type='application/json', status=403)
          print("Staging base path is: " + STAGING["target_path_base"]+'/'+basepath)
          request_url = STAGING["service"]
          endpoint = "stage"
          ss = STAGING["zones"][zone]
          if ss is None:
             session.cleanup()
             return None, MalformedRequest ("Unknown Zone: "+zone)
          if flags[1] == "yes": # compression
             res = get_compressed_file (session, fullirodspath+'/'+name)
             if res[1] != None:
                session.cleanup()
                return HttpResponse ('{"status": 503, "error_string": "Error retrieving compressed dataset: %s"}'%res[1], 
                                  status= 503)
             if subpath != "":
                 if subpath != res[0]:
                    session.cleanup()
                    return None, MalformedRequest("Path does not match filename of compressed dataset")
             else:
                irodsroute = getIrodsPathNoZone(access, user, project) + '/' + name + '/' + res[0]
             
          json_body={
                 "source_system" : STAGING["zones"][zone], 
                 "source_path": irodsroute,
	         "target_system": STAGING["target_system"] ,
	         "target_path": STAGING["target_path_base"]+'/'+basepath,
                 "encryption": flags[0],
                 "compression": flags[1]}
          resp, err = callStaging_Enc(request_url, endpoint, token, json_body, localpath)
          if err is not None:
            session.cleanup()
            return None, err
          if resp.json()["status"] == "Task Failed, reason: Dataset doesn't exist or wrong target path":
            session.cleanup()
            return None, MalformedRequest ("Wrong path")
          if flags[1] == "yes": # staging adds an extra directory
             extra = os.path.basename(resp.json()["target_path"]) 
          if subpath == "":
            if flags[1] == "yes":
               datasetpath=localpath+'/'+extra
            else:
               datasetpath=localpath+'/'+name
            print("datapath with name is: " + datasetpath)
          else:
          #https://stackoverflow.com/questions/3925096/how-to-get-only-the-last-part-of-a-path-in-python
            di=os.path.basename(os.path.normpath(subpath))
            if flags[1] == "yes":
               datasetpath=localpath+'/'+extra
            else:
               datasetpath=localpath+'/'+di
          if multipart is None:
              try:
                di=os.path.basename(os.path.normpath(datasetpath))
                print ("content of zip should be: ", localpath+'/'+di)
                while True:
                  try:
                    time.sleep (5)
                    shutil.make_archive (localpath+"/dataset", 'zip', localpath, di)
                    break
                  except FileNotFoundError:
                    pass

              except NotADirectoryError:
                with ZipFile(localpath+"/dataset.zip","w") as myzip:
                  myzip.write(datasetpath, di)
          else:
              try:
                res=os.system("zip -s "+multipart+"m -r "+localpath+"dataset.zip "+datasetpath)
                print("multipart is: " + "zip -s "+multipart+"m -r "+localpath+"dataset.zip "+datasetpath)
              except:
                  session.cleanup()
                  return None, HttpResponse('{"status": "503", "errorString": "Error creating compressed file"}',
                                             content_type='application/json', status=503)
          return localpath, None
          print ("response "+resp)
    except requests.exceptions.SSLError:
        shutil.rmtree(localpath)
        session.cleanup()
        return None, HttpResponse ('{"status": "503", "errorString": "Error connecting to staging backend, SSL Error"}',
                             content_type='application/json', status=503)

    except requests.exceptions.ConnectionError:
          shutil.rmtree(localpath)
          session.cleanup()
          return None, HttpResponse ('{"status": "503", "errorString": "Error connecting to staging backend"}',
                             content_type='application/json', status=503)

    except json.decoder.JSONDecodeError:
          session.cleanup()
          return None, MalformedRequest("Invalid json")
    except KeyError:
          session.cleanup()
          return None, MalformedRequest("Required Field missing")
        #json only
        #PUT creates a new dataset
        #{push_method="ssh", "grid", "globus", "directupload",
        #file="file contents", used in directupload
        #URL="url", used in others
        #name="dataset name",
        #access="user", "group", "project", "public"
        #project=""
        #group=""
#metadata=[]
#compress_method='file' 'tar' 'targz', ...
#}
#receive an identifier back (collectionid), which can be low-level queried to see if complete/obsolete (error in transfer)/in progress
@csrf_exempt
def uploadDatasetAPI(request):
    (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
    if err is not None:
        return err
    with GetSession (dditoken, user) as session:
      try:
          #https://stackoverflow.com/questions/22394235/invalid-control-character-with-python-json-loads
          q=json.loads(request.body.decode('utf-8'))
          internalID=q.get('internalID', None)
          path=q.get('path', "")
          if internalID is None and path != "":
             session.cleanup()
             revokeToken(dditoken)
             return MalformedRequest("Path provided for new dataset")
          access=q['access']
          project=q['project']
          metadata=q.get('metadata', None)
          method=q['push_method']
          if method != "empty" and method != "directupload" and method != "tus":
              session.cleanup()
              revokeToken(dditoken)
              return MalformedRequest("push_method not allowed")
          compress=q.get('compress_method', 'file')
          err=DatasetCheckPermission(session, access, user, project, dditoken, attr)
          if err is not None:
             session.cleanup()
             revokeToken(dditoken)
             return err
          filecontent=q.get('file', "")
          filename=q.get("name", None)
          enc=q.get("enc", "no")
          comp=q.get("comp", "no")
          zone = q.get('zone', IRODS['zone'])
          r= uploadDatasetInternal(session, user, internalID, access, project, zone, path, method, compress, filecontent, 
		filename, metadata, dditoken, enc, comp)
          session.cleanup()
          revokeToken(dditoken)
          return r
      except json.decoder.JSONDecodeError:
          session.cleanup()
          revokeToken(dditoken)
          return MalformedRequest("Invalid JSON")
      except KeyError:
          session.cleanup()
          revokeToken(dditoken)
          return MalformedRequest("Needed field missing")
      except ExceptionOpenIDAuthUrl:
          session.cleanup()
          revokeToken(dditoken)
          return AuthURL()

def verifyMetadataForUpload (metadata, session, user, project, access):
    """Verify a metadata against the schemas and return them

    Parameters
    ----------
    metadata : iRODS metadata 
    session : iRODS object
        A session iRODS object to access iRODS.
    user : String
        The irods username
    project : String
        The ddi project

    Return 
    ------
    error or None 
    """
    if (metadata is not None):
      schemas=metadata.get("CustomMetadataSchema", None)
      custom=metadata.get("CustomMetadata", None)
      if custom is not None or schemas is not None:
        for idx, schema in enumerate(schemas):
          try:
            validate(instance=custom, schema=schema)
          except jsonschema.exceptions.ValidationError:
            return (MalformedRequest("CustonMetadata not validated by schema "+str(idx)))
      for x in metadataSingleValue:
            val=metadata.get (x, None)
            if val != None and not isinstance(val, str):
               return (MalformedRequest("Metadata "+x+" is not a string"))
      for x in metadataMultiValue:
            val=metadata.get (x, None)
            if val is not None and not isinstance (val, list):
               return (MalformedRequest("Metadata "+x+" is not an array"))

      ais = metadata.get("AlternateIdentifier", None)
      if ais is not None:
          for ai in ais:
              if not isinstance (ai, list) or len(ai) != 2:
                 return (MalformedRequest("Metadata AlternateIdentifier should be an array of pairs of strings"))
              if not isinstance (ai[0], str) or not isinstance (ai[1], str):
                 return (MalformedRequest("Metadata AlternateIdentifier should be an array of pairs of strings"))
    if access == 'public':
      res=group.check_adm_user_project_membership(session, user, project)
      try:
        right=metadata["rightsURI"][0]
      except:
        return MalformedRequest("rightsURI metadata required for public data")
    elif access=='project' or access == 'user':
      res=group.check_user_project_membership(session, user, project)
    else:
      return MalformedRequest("Access should be user, project or public")
    if res==False:
      return E403()
    return None

def compress_encrypt_directory (localpath, enc, comp, project, url, json_body, token):
    if enc == "no" and comp == "no":
        return localpath, None
    elif enc == "no" and comp == "yes":
        resp, err = callStaging_Enc(url, "compress", token, json_body, localpath)
    elif enc == "yes" and comp == "no":
        resp, err = callStaging_Enc(url, "encrypt", token, json_body, localpath)
    elif enc == "yes" and comp == "yes":
        resp, err = callStaging_Enc(url, "compress_encrypt", token, json_body, localpath)
    return resp, err

def uploadDatasetInternal(session, user, internalID, access, project, zone, path, method, compress, filecontent,
                          filename, metadata, token, enc="no", comp="no"):
    try:
        # Validate required metadata format
        verify_error = verifyMetadataForUpload(metadata, session, user, project, access)
        if verify_error is not None:
            return verify_error

        # Check if method is allowed
        if method not in ["directupload", "empty", "tus"]:
            return HttpResponse('{"status": "400", "errorString": "Unsupported push_method"}',
                                content_type='application/json', status=400)

        # Get full path to this dataset in the DDI
        irodspath = getIrodsPath(access, user, project, zone)

        # Handle creating or updating new dataset
        if not internalID or internalID == "":
            # Generate DDI dataset ID for new dataset
            dataset_id = str(uuid.uuid1())
        else:
            # Dataset ID was passed, it will be updated
            dataset_id = internalID
            # Check if this dataset exists in DDI
            try:
                session.collections.get(irodspath+"/"+dataset_id)
                # Append the passed path to the dataset irods path
                irodspath = os.path.join(irodspath, dataset_id, path)
            except CollectionDoesNotExist as ce:
                logger.error("Dataset ID: {0} does not exist in the DDI ({1})".format(dataset_id, ce))
                return MalformedRequest("Dataset ID: {0} does not exist in the DDI.".format(dataset_id))

        # Get staging directory and path to the uploaded file
        dataset_staging_dir = os.path.join(STAGING['path'], dataset_id)
        if filename is not None:
           staged_file_path = os.path.join(dataset_staging_dir, filename)

        # Create staging path
        try:
            #cleanup
            try:
              shutil.rmtree(dataset_staging_dir)
            except:
              pass
            os.mkdir(dataset_staging_dir)
        except OSError:
            logger.error("Unable to create staging directory: {0}".format(dataset_staging_dir))
            return MalformedRequest("Unable to create staging directory.")

        # Direct upload in POST (base64 encoded file in field "file")
        if method == 'directupload':
            try:
                with open(staged_file_path, 'wb') as f:
                    x = filecontent.replace ("\n", "") # python b64decode does not like newlines
                    f.write(base64.b64decode(x, validate=True))
            except OSError:
                shutil.rmtree(dataset_staging_dir)
                return MalformedRequest("Unable to write file to staging area.")
            except binascii.Error:
                shutil.rmtree(dataset_staging_dir)
                return MalformedRequest("Unable to decode base64 encoded file.")

        # Retrieve file uploaded with TUS
        if method == "tus":
            try:
                # Save TUS upload
                resource_id = filecontent.split('/')[len(filecontent.split('/'))-1:][0]
                uploaded_file = UploadedFile.objects.get(filename=filename, project=project, user=user, tusresourceid=resource_id)
                tus_uploaded_path = os.path.join(settings.TUS_DESTINATION_DIR, uploaded_file.filenameondisk)

                # Move the uploaded file to staging directory
                shutil.move(tus_uploaded_path, staged_file_path)
                uploaded_file.delete()

            except shutil.ReadError:
                shutil.rmtree(dataset_staging_dir)
                return MalformedRequest("TUS upload not found")

            except ObjectDoesNotExist:
                shutil.rmtree(dataset_staging_dir)
                return MalformedRequest("TUS upload not found")

            except MultipleObjectsReturned:
                logger.error("Duplicated TUS uploads have been found for filename: {0}".format(filename))
                shutil.rmtree(dataset_staging_dir)
                return MalformedRequest("File is already uploaded in TUS.")
            except ProgrammingError:
                return HttpResponse ('{"errorString": "Backend misconfiguration, tus database"}', status=502)
            except Exception as e:
                logger.error ("Exception on /dataset; type tus. "+str(e))
                return HttpResponse ('{"errorString": "Backend misconfiguration: '+str(e)+'"}', status=502)

        # Uncompress uploaded data if zip flag is present
        if compress == 'zip':
            try:
                shutil.unpack_archive(staged_file_path, extract_dir=dataset_staging_dir, format='zip')
            except shutil.ReadError:
                shutil.rmtree(dataset_staging_dir)
                return MalformedRequest("File not in ZIP format")
            finally:
                os.remove(staged_file_path)

        # Dataset ready for compression, encryption and pushing to DDI
        url = STAGING["encryption_service"]
        json_body = {
            "source_system": STAGING["target_system"],
            "source_path": dataset_staging_dir,
            "project": project}
        resp, err = compress_encrypt_directory(dataset_staging_dir, enc, comp, project, url, json_body, token)
        if err is not None:
            logger.error("Unable to compress/encrypt dataset: {0}".format(err))
            return MalformedRequest("Unable to compress/encrypt dataset.")

        if enc == "no" and comp == "no":
            dataset_staging_dir = resp
        else:
            abs_path = os.path.relpath(resp.json()["target_path"], STAGING['internal_path'])
            dataset_staging_dir = STAGING['path'] + "/" + abs_path

        # Push dataset to iRODS
        try:
            if internalID is None or comp == "yes":
                irods_transfer.iput(session, dataset_staging_dir, irodspath, user, IRODS['federated'])
            else:
                # Get path in current dataset based on body parameter "path"
                dataset_path = os.path.join(irodspath, path)
                if dataset_path[-1]=='/':
                   dataset_path = dataset_path[:-1]
                # List the staging directory and push it inside the dataset
                for file in os.listdir(dataset_staging_dir):
                    if os.path.isfile(os.path.join(dataset_staging_dir, file)):
                        irods_transfer.iputFile(session, dataset_staging_dir, dataset_path, file,
                                                user, IRODS['federated'])
                    elif os.path.isdir(os.path.join(dataset_staging_dir, file)):
                        irods_transfer.iput(session, os.path.join(dataset_staging_dir, file), dataset_path,
                                            user, IRODS['federated'])

            # Remove dataset staging dir on successful transfer
            shutil.rmtree(dataset_staging_dir)

        except iRODSException as ie:
            logger.error("iRODS exception when pushing uploaded dataset: {0}".format(ie))
            return MalformedRequest("Error occured when pushing dataset to iRODS")
        except SYS_INTERNAL_NULL_INPUT_ERR:
            return HttpResponse(
                '{"errorString": "User does not have permission to access dataset, or dataset does not exist"}',
                content_type='application/json', status=403)

        # Add metadata to iRODS
        if metadata is not None:
               try:
                  if internalID is not None:
                     ip = irodspath
                     if ip[-1]=='/':
                        ip = irodspath[:-1]
                     coll=session.collections.get(ip)
                  else: 
                     coll=session.collections.get(irodspath+'/'+dataset_id)
               except CollectionDoesNotExist:
                  print (irodspath)
                  return HttpResponse ('{"errorString": "Error retrieving collection for metadata upload"}', 
                             content_type='application/json', status=403)
               for key in coll.metadata.keys():
                   eudat=False
                   for e in metadataEUDAT:
                       if e==key:
                           eudat=True
                   if not eudat:
                     for item in coll.metadata.get_all(key):
                         coll.metadata.remove(item)
               coll.metadata.add ('access', access)
               coll.metadata.add ('project', project)
               coll.metadata.add ('user', user)
               coll.metadata.add ('encryption', enc)
               coll.metadata.add ('compression', comp)
               for x in metadataSingleValue:
                try:
                  val=metadata[x]
                  if x=="CustomMetadata":
                     coll.metadata.add(x, json.dumps(val))
                  else:
                     coll.metadata.add(x, str(val))
                except:
                  print('Metadata for ' + x + ' missing')
#return error later or add to warning list
             
               for x in metadataMultiValue:
                try:
                  val=metadata[x]
                  if not isinstance(val, str):
#Should be list instead and we don't want python to separate string into individual letters
                     for y in val:
                       if x=="CustomMetadataSchema" or x=="AlternateIdentifier": 
                           coll.metadata.add(x, json.dumps(y))
                       else:
                           coll.metadata.add(x, y)
                  else:
                     return MalformedRequest("%s should be array."%x);
                except:
                  print('Metadata for ' + x + ' missing or not array')
        # Return 201 created on creation of new dataset, 200 on update
        returned_id = dataset_id
        if internalID is None:
            status_code = 201
        else:
            status_code = 200

        return HttpResponse('{"status": "%d", "internalID": "%s"}' % (status_code, returned_id),
                            content_type='application/json', status=status_code)

    except (FileNotFoundError, PermissionError):
        return HttpResponse('{"errorString": "Server misconfiguration"}',
                            content_type='application/json', status=500)
    except RequestDataTooBig:
        return HttpResponse('{"errorString": "Maximum file size exceeded, use a different transfer method"}',
                            content_type='application/json', status=400)

    except json.decoder.JSONDecodeError:
        return MalformedRequest("Invalid JSON")

    except KeyError:
        return MalformedRequest("Needed field missing")

    except CAT_NO_ACCESS_PERMISSION:
        return HttpResponse('{"errorString": "Backend misconfiguration: possibly user directory does not exist"}',
                            content_type='application/json', status=503)
    except CAT_SQL_ERR:
        return HttpResponse('{"errorString": "Error in iRODS database backend"}',
                            content_type='application/json', status=503)
    except SYS_INVALID_INPUT_PARAM:
        return MalformedRequest("Wrong iRODS zone")

@csrf_exempt
def Datasets(request):
    if request.method=='POST':
       return uploadDatasetAPI(request)
    elif request.method=='DELETE':
       return deleteDatasetAPI(request)
    return E405()

@csrf_exempt
def DatasetDownload(request):
  if request.method=='POST':
     return downloadDatasetAPI(request)
  return E405()

def gatherDataC(session, colls):
        i=[]
        for r in colls:
           d={}
           d['internalID']=r[0].name
           d['access']=r[1]["access"]
           d['project'] = r[1]["project"]
           d['zone'] = r[1]["zone"]
           m={}
           datasetMeta(m, r[0].metadata)
           m['CreationDate']=r[0].create_time.strftime("%Y-%m-%dT%H:%M:%SZ")
           e={}
           datasetEudat(e, r[0].metadata)
           f={}
           datasetEncComp(f, r[0].metadata)
           i.append({"location": d, "metadata": m, "eudat": e, "flags": f})
        return i

def CollChecks(coll, checks, access):
    for key in checks:
        if key=="AlternateIdentifier" or key=="AlternateIdentifierType":
            continue # semantics is that these are together, otherwise [[a,b],[c,d]] matches [a,d]
        if key=="internalID":
            if re.search (checks[key], coll.name, re.IGNORECASE) is None:
              return False
        elif key=="access":
            if checks[key] != access["access"]:
              return False
        else:
          found = False
          for y in coll.metadata.get_all(key):
            #if y.value == str(checks[key]):
            if key=="CustomMetadata":
               found = checkCustom (checks[key], json.loads(y.value));
            elif re.search (checks[key], y.value, re.IGNORECASE):
               found= True
               break
          if found == False:
             return False
    if "AlternateIdentifier" in checks or "AlternateIdentifierType" in checks:
        ai=checks.get("AlternateIdentifier", "")
        ait=checks.get("AlternateIdentifierType", "")
        for y in coll.metadata.get_all("AlternateIdentifier"):
            pair=json.loads(y.value)
            if re.search (ait, pair[0]) and re.search (ai, pair[1]):
               return True
        return False
        
    return True

def findCols(coll, checks, access):
    cols=[]
    for col in coll.subcollections:
            res= CollChecks (col, checks, access)
            if res == True:
               cols.append([col, access])
    return cols

def findColsAll(token, user, session, checks, listableprojects):
    l=[]
    coll_not_exist = []
    for zone in [IRODS['zone']] + IRODS['federated']:
        path = '/' + zone + '/public'
        try:
            collpublic=session.collections.get(path)
            for x in collpublic.subcollections:  # projects
                try:
                    shortp = x.metadata.get_one("ShortProject").value
                    l += findCols(x, checks, {"access": "public", "project": shortp, "zone": zone})
                except CollectionDoesNotExist:
                    coll_not_exist.append(path + '/' + x.name)
        except CollectionDoesNotExist:
            coll_not_exist.append(path)


        userprojects=[]
        try:
            for up in session.collections.get('/' + zone + '/project').subcollections:
                try:
                   userprojects.append([up.name, up.metadata.get_one("ShortProject").value])
                except CollectionDoesNotExist:
                   coll_not_exist.append('/' + zone + '/project' + up.name)
        except CollectionDoesNotExist:
            coll_not_exist.append('/' + zone + '/project')

        for x in userprojects:
            if x[1] in listableprojects:
                userpath = '/'+zone+'/user/'+x[0]+'/'+user
                try:
                    p=session.collections.get(userpath)
                    l+=findCols (p, checks, {"access": "user", "project": x[1],"zone": zone})
                except CollectionDoesNotExist:
                    coll_not_exist.append(userpath)

        try:
            zone_project_coll = session.collections.get('/'+zone+'/project')
            for x in zone_project_coll.subcollections:
                try:
                    shortp = x.metadata.get_one("ShortProject").value
                    if shortp in listableprojects:
                        l += findCols(x, checks, {"access": "project", "project": shortp, "zone": zone})
                except CollectionDoesNotExist:
                    coll_not_exist.append(shortp)
        except CollectionDoesNotExist:
            coll_not_exist.append('/'+zone+'/project')



    if len(coll_not_exist) > 0:
        logger.error("Collection does not exist or permission denied for user {0} at: \n{1}".format(user,"\n".join(coll_not_exist)))

    return l


def getProjectFromiRODSPath (session, irodspath):
    comp = irodspath.split ("/")
    projpath = comp[0]+'/'+comp[1]+'/'+comp[2]
    coll = session.collections.get(projpath)
    project = coll.metadata.get_one("ShortProject").value
    return project

@csrf_exempt
def SearchMeta(request):
#API, pass as json an array with the query terms: e.g. ["Year": "1900", "Author": "1"]
    (dditoken, user, refresh, token, attr, err)=GetUserAndTokenAPI(request)
    if err is not None:
       return err
    with GetSession(dditoken, user) as session:
#Multiple filters on the same column overwrite, so 
#imeta qu -C publicationYear = 1900 and relatedIdentifier = "doi://lexis-datasets/wp5/datasetpublicx1"
#does not work. Doing the set-intersection ourselves is one possibility, or going through all collections recursively.
#https://github.com/irods/python-irodsclient/issues/135#issuecomment-564554609
#https://github.com/irods/python-irodsclient/issues/135
#rgh: after applying the patch, this should now work
        try:
          q=json.loads(request.body.decode('utf-8'))
          listableprojects=getListableProjects (attr)
          try:
            results = findColsAll(dditoken, user, session, q, listableprojects)
          except struct.error: 
            session.cleanup()
            revokeToken(dditoken)
            return HttpResponse ('{"errorString": "Irods-keycloak connection failed"}', content_type='application/json', status=503)
          if results is None: #bad token
             session.cleanup()
             revokeToken(dditoken)
             return HttpResponse ('{"errorString": "Token does not provide projects information"}',  content_type='application/json', status=503)
        except ExceptionOpenIDAuthUrl:
          session.cleanup()
          revokeToken(dditoken)
          return AuthURL()
        except CollectionDoesNotExist as e:
            session.cleanup()
            return HttpResponse ('{"errorString": "Irods permissions too restrictive for this user: %s"}'%e, content_type='application/json', status=503)
        except NetworkException:
          session.cleanup()
          revokeToken(dditoken)
          return HttpResponse ('{"errorString": "Error connecting to irods backend"}', content_type='application/json', status=503)
        except json.decoder.JSONDecodeError:
          session.cleanup()
          revokeToken(dditoken)
          return MalformedRequest("Invalid JSON");
        except KeyError:
          session.cleanup()
          revokeToken(dditoken)
          return HttpResponse ('{"errorString": "Irods misconfiguration (ShortProject)"}', content_type='application/json', status=503)
#       except :
#          return HttpResponse ('{"status": "503", "errorString": "Unexpected error connecting to irods backend"}', content_type='application/json', status=503)
#get method would mean we cannot use body content to adapt response
        if request.method=='POST':
          try:
            i=gatherDataC(session, results)
            session.cleanup()
            revokeToken(dditoken)
            return HttpResponse (json.dumps(i, sort_keys=True, indent=4), content_type='application/json')
          except NetworkException:
            session.cleanup()
            revokeToken(dditoken)
            return HttpResponse ('{"errorString": "Unable to contact backend iRODS service"}', status=502)
        elif request.method=='DELETE':
          logger.info("deleting")
          noPerm=[]
          for r in results:
            try:
              r[0].remove()
            except CAT_NO_ACCESS_PERMISSION:
              noPerm.append(r)
              logger.info("not deleted: %s"%r[0].name)
          if noPerm==[]:
            logger.info("204")
            session.cleanup()
            revokeToken(dditoken)
            return HttpResponse (status=204)
          else:
            logger.info("403")
            resp={"errorString": "Some collections were not deleted due to insufficient permissions by user"}
            res=[]
            for c in noPerm:
                 res.append({"internalID":c[0].name})
            resp["permission_error"]=res
            session.cleanup()
            revokeToken(dditoken)
            return HttpResponse (json.dumps(resp), content_type='application/json', status=403)
        else:
            session.cleanup()
            revokeToken(dditoken)
            return E405();


def get_compressed_file (session, dataset_coll):
   try:
     dataset = session.collections.get(dataset_coll)
     size = len(dataset.data_objects)
     if size != 1:
        return [ None, "More than one file found in a compressed dataset" ]
     o = dataset.data_objects[0].name
     return [o, None]
   except CollectionDoesNotExist:
     return [ None, 404 ]

def get_encryption_compression_meta( session, dataset_coll):
   try:
     dataset = session.collections.get(dataset_coll)
   except CollectionDoesNotExist:
     return [ None, None, 404 ]
   try:
     enc_flag = dataset.metadata.get_one("encryption").value
     comp_flag = dataset.metadata.get_one("compression").value
     return [enc_flag, comp_flag, None]
   except:
     return ["no", "no", None]
   #except:
   #  return [ "encryption flag doesn't exist or dataset doesn't exist", "compression flag doesn't exist or dataset doesn't exist"]
