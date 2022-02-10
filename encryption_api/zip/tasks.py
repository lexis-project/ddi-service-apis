from celery import Celery
import logging
import time
from celery import states
from celery.exceptions import Ignore
from celery.result import AsyncResult
from encryption_api.celery import app
from . import irods_transfer
import sys
import os
import subprocess
import random
import shutil
import string
import uuid
import yaml

import pdb

with open("/etc/staging_api/system.yml") as file:
        systems = yaml.load(file, Loader=yaml.FullLoader)

@app.task(bind=True)
def zip(self,source_system, source_path, token, size, cleanup=False):
  time.sleep(3)
  try:
    sys.stdout.write("Before zip")
    base = systems["systems"][source_system]["base_path"]
    path2=str(uuid.uuid1())
    time.sleep(3)
    self.update_state(meta={'custom': 'Preparing ZIP'})
# zip -s 10M -r finished/path-2/dataset.zip in_progress/path-1/edcca382-b1a4-11ea-8c4e-0050568fc9b5  
    p1=base + source_path
    p2=base+"multipart/finished/"+path2
    if not (os.path.exists(p1)):
      raise Exception("Source dataset doesn't exist")
    os.mkdir(p2)
    os.chdir(p1)
    password=''.join(random.choice(string.ascii_lowercase) for i in range(10))
    line = "zip -e -P "+password+" -q --display-globaldots -ds 10M -r -s "+str(size)+"M "+p2+"/dataset.zip *"
    sys.stdout.write(line)
    #ret=os.system (line)
    shell = True
    count = 0
    popen = subprocess.Popen(line, shell=shell, stdout=subprocess.PIPE)
    while True:
        c = popen.stdout.read(1)
        if c==b".":
           count =count +1
        print (count*10, "megabytes processed")
        self.update_state(meta={'custom': str(count*10)+ " megabytes processed"})
        if popen.poll() is not None:
           print ("Finished zipping")
           self.update_state(meta={'custom': "Finished zipping"})
           break

    popen.wait()
    if popen.returncode != 0:
       sys.stdout.write("Problem creating zip files")
       self.update_state(state=states.FAILURE, meta={'custom': 'Problem creating zip files'})
       raise Ignore()
    else:
        if cleanup:
           shutil.rmtree(p1)
    
    l=os.listdir(p2)
    l2=sorted(["multipart/finished/"+path2+"/"+f for f in l])
    return [app.current_task.request.id, l2, password]
  except Exception as e:
      sys.stdout.write("Exception when creating zip: "+str(e))
      self.update_state(state=states.FAILURE, meta={'custom': str(e),
          'exc_type': type(e).__name__,
          'exc_message': str(e)})
      sys.stdout.write(str(self.AsyncResult(self.request.id).state))
      raise Ignore()
    
