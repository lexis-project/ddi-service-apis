import logging
from django.urls import reverse
from encryption_api.celery import app
from celery import states
from celery.exceptions import Ignore
from celery.result import AsyncResult
from celery import Celery
from . import encryption_api


@app.task(bind=True)
def encrypt(self, input_data):
    logging.info("Starting encryption")
    try:
        # encryption function here
        encryption = encryption_api.encrypt(input_data)
    except Exception as e:
        logging.info("Handling exception in encryption")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        logging.info(str(e))
        data = self.request.chain
        if data is not None:
            logging.info(str(data))
            last_task = str(data[0]["options"]["task_id"])
            logging.info(last_task)
            self.update_state(
                task_id=last_task,
                state=states.FAILURE,
                meta={
                    'custom': str(e),
                    'exc_type': type(e).__name__,
                    'exc_message': str(e)})
            self.request.chain = None
        raise Ignore()
    return [app.current_task.request.id, encryption]


@app.task(bind=True)
def decrypt(self, input_data):
    logging.info("Starting decryption")
    try:
        # encryption function here
        decryption = encryption_api.decrypt(input_data)
    except Exception as e:
        logging.info("Handling exception in decryption")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        logging.info(str(e))
        data = self.request.chain
        if data is not None:
            logging.info(str(data))
            last_task = str(data[0]["options"]["task_id"])
            logging.info(last_task)
            self.update_state(
                task_id=last_task,
                state=states.FAILURE,
                meta={
                    'custom': str(e),
                    'exc_type': type(e).__name__,
                    'exc_message': str(e)})
            self.request.chain = None
        raise Ignore()
    return [app.current_task.request.id, decryption]


@app.task(bind=True)
def compress_encrypt(self, input_data):
    logging.info("Starting encryption + compression")
    try:
        # encryption function here
        encryption = encryption_api.compress_encryt(input_data)
    except Exception as e:
        logging.info("Handling exception in encryption + compression")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        logging.info(str(e))
        data = self.request.chain
        if data is not None:
            logging.info(str(data))
            last_task = str(data[0]["options"]["task_id"])
            logging.info(last_task)
            self.update_state(
                task_id=last_task,
                state=states.FAILURE,
                meta={
                    'custom': str(e),
                    'exc_type': type(e).__name__,
                    'exc_message': str(e)})
            self.request.chain = None
        raise Ignore()
    return [app.current_task.request.id, encryption]


@app.task(bind=True)
def decrypt_decompress(self, input_data):
    logging.info("Starting decryption + uncompression")
    try:
        # encryption function here
        decryption = encryption_api.decrypt_decompress(input_data)
    except Exception as e:
        logging.info("Handling exception in decryption + compresion")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        logging.info(str(e))
        data = self.request.chain
        if data is not None:
            logging.info(str(data))
            last_task = str(data[0]["options"]["task_id"])
            logging.info(last_task)
            self.update_state(
                task_id=last_task,
                state=states.FAILURE,
                meta={
                    'custom': str(e),
                    'exc_type': type(e).__name__,
                    'exc_message': str(e)})
        raise Ignore()
    return [app.current_task.request.id, decryption]


@app.task(bind=True)
def compress(self, input_data):
    logging.info("Starting compression")
    try:
        compression = encryption_api.compress(input_data)
    except Exception as e:
        logging.info("Handling exception in compression")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        logging.info(str(e))
        data = self.request.chain
        if data is not None:
            logging.info(str(data))
            last_task = str(data[0]["options"]["task_id"])
            logging.info(last_task)
            self.update_state(
                task_id=last_task,
                state=states.FAILURE,
                meta={
                    'custom': str(e),
                    'exc_type': type(e).__name__,
                    'exc_message': str(e)})
            self.request.chain = None
        raise Ignore()
    return [app.current_task.request.id, compression]


@app.task(bind=True)
def decompress(self, input_data):
    logging.info("Starting compression")
    try:
        decompression = encryption_api.decompress(input_data)
    except Exception as e:
        logging.info("Handling exception in decompression")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        logging.info(str(e))
        data = self.request.chain
        if data is not None:
            logging.info(str(data))
            last_task = str(data[0]["options"]["task_id"])
            logging.info(last_task)
            self.update_state(
                task_id=last_task,
                state=states.FAILURE,
                meta={
                    'custom': str(e),
                    'exc_type': type(e).__name__,
                    'exc_message': str(e)})
            self.request.chain = None
        raise Ignore()
    return [app.current_task.request.id, decompression]
