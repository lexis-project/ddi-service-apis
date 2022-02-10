from datetime import datetime
from django.test import TestCase, LiveServerTestCase
import logging
import os
import shutil
from transfer import test_util
import uuid
import jwt
from tusclient import client
import requests
import time
import yaml

logger = logging.getLogger(__name__)
# logging.disable(logging.NOTSET)
# logger.setLevel(logging.DEBUG)

RANDOM_FILE_SIZE = 10 # MB
TEST_DATASET_PATH = '/tmp/transfer_api_{0}'.format(uuid.uuid1())

class UploadTest(LiveServerTestCase):

    _test_files = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logger.info("Generating random file for upload")
        
        
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DATASET_PATH, ignore_errors=True)
        super().tearDownClass()

    
    def setUp(self):
        super().setUp()
       
        
    def testUploadSingleFile(self):
        token = test_util.get_token()
        self.assertIsNotNone(token)

        logger.info(self.live_server_url)
        test_files = test_util.generate_dataset(TEST_DATASET_PATH)
        logger.info(test_files)


        tusclient = client.TusClient(self.live_server_url + '/transfer/upload/', headers={'Authorization': 'Bearer ' + token})

        uploader = tusclient.uploader(test_files[0][0], log_func=logger.info,
                metadata= {
                    'filename': 'data.dat',
                    'path': 'dataset',
                    'user': 'demo_data_manager',
                    'project': 'demoproject',
                    'zone': 'it4i_iRODS',
                    'access': 'project',
                    'token': token,
                    'metadata': "",
                    'encryption': 'no'
                })

        # Uploads the entire file.
        # This uploads chunk by chunk.
        uploader.chunk_size = 1024*1024
        uploader.upload()

        loops = 0
        succcess = False
        while loops < 50 or not succcess:
            req = requests.get(self.live_server_url + '/transfer/status', headers={'Authorization': 'Bearer ' + token}).json()
            if req[0]['task_state'] == 'SUCCESS':
                succcess = True
                break

            loops = loops + 1
            time.sleep(1)

        self.assertTrue(succcess)
        