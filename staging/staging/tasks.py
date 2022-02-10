import logging
import time
from django.urls import reverse
from staging_api.celery import app
from celery import states
from celery.exceptions import Ignore
from celery.result import AsyncResult
from celery import Celery
from . import data_size
from . import replication_api
from . import staging_api
import sys
import os


@app.task(bind=True)
def stage_class_1(self, input_data, clean_source=False, revoke_token=False):
    logging.info("Starting Class 1 data trasnfer")
    try:
        # class 1 staging function
        transfer = staging_api.irods_to_nfs(input_data, clean_source, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 1 transfer")
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def stage_class_2(self, input_data, clean_source=False, revoke_token=False):
    logging.info("Starting Class 2 data trasnfer")
    try:
        # class 2 staging function
        transfer = staging_api.nfs_to_irods(input_data, clean_source, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 2 transfer")
        logging.info("Dumping input data")
        logging.info(input_data)
        logging.info(str(e))
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def stage_class_3(self, input_data, clean_source=False, revoke_token=False):
    logging.info("Starting Class 3 data trasnfer")
    try:
        # class 3 staging function
        transfer = staging_api.nfs_to_nfs_transfer(input_data, clean_source, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 1 transfer")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def stage_class_4(self, input_data, revoke_token=False):
    logging.info("Starting Class 4 data trasnfer")
    try:
        # class 4 staging function
        transfer = staging_api.irods_to_local_hpc(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 4 transfer")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def stage_class_5(self, input_data, revoke_token=False):
    logging.info("Starting Class 5 data trasnfer")
    try:
        # class 5 staging function
        transfer = staging_api.local_hpc_to_irods(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 5 transfer")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def stage_class_6(self, input_data, clean_source=False, revoke_token=False):
    logging.info("Starting Class 6 data trasnfer")
    try:
        # class 6 staging function
        transfer = staging_api.nfs_to_local_hpc(input_data, clean_source, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 6 transfer")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def stage_class_7(self, input_data, revoke_token=False):
    logging.info("Starting Class 7 data trasnfer")
    try:
        # class 7 staging function
        transfer = staging_api.local_hpc_to_nfs(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 7 transfer")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def preprocess_input(self, input_data):
    logging.info("Starting preprocessing")
    try:
        sys.stdout.write(str(staging_api.prepare_input_to_iRODS(input_data)))
    except Exception as e:
        logging.info("Handling exception in preprocessing")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return staging_api.prepare_input_to_iRODS(input_data)


@app.task(bind=True)
def postprocess_input(self, transfer_output, input_data):
    logging.info("Starting postprocessing")
    try:
        input_data["source_system"] = staging_api.get_local_irods()
        base_path = staging_api.get_base_path(input_data["source_system"])
        source_path = os.path.relpath(transfer_output[1], base_path)
        input_data["source_path"] = source_path
    except Exception as e:
        logging.info("Handling exception in preprocessing")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return input_data


@app.task(bind=True)
def delete_class_1(self, input_data):
    logging.info("Starting Class 1 deletion")
    revoke_token = True
    try:
        staging_api.delete_irods(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 1 deletion")
        logging.info("Dumping input data")
        logging.info(input_data)
        logging.info(str(e))
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id]


@app.task(bind=True)
def delete_class_2(self, input_data):
    logging.info("Starting Class 2 deletion")
    revoke_token = True
    try:
        staging_api.delete_nfs(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 2 deletion")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id]


@app.task(bind=True)
def delete_class_3(self, input_data):
    logging.info("Starting Class 3 deletion")
    revoke_token = True
    try:
        staging_api.delete_hpc(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in Class 3 deletion")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id]


@app.task(bind=True)
def get_data_size(self, input_data):
    logging.info("Starting the get data size task")
    try:
        size = data_size.get_data_size(input_data)
        logging.info(size)
    except Exception as e:
        logging.info("Handling exception in data size class")
        logging.info("Dumping input data")
        logging.info(str(e))
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id, size]


@app.task(bind=True)
def replicate(self, input_data):
    logging.info("Starting the replication task")
    try:
        replication = replication_api.initiate_replication(input_data)
    except Exception as e:
        logging.info("Handling exception in replication class")
        logging.info("Dumping input data")
        logging.info(str(e))
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        sys.stdout.write(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id, replication]


@app.task(bind=True)
def assign_pid(self, input_data):
    logging.info("Starting the PID assignment task")
    try:
        pid = replication_api.initiate_pid_assignment(input_data)
    except Exception as e:
        logging.info("Handling exception in PID assignment class")
        logging.info("Dumping input data")
        logging.info(str(e))
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        sys.stdout.write(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id, pid]


@app.task(bind=True)
def prepare_encryption1(self, input_data):
    logging.info("Starting preparation for encryption api 1")
    try:
        data = staging_api.prepare_encryption1(input_data)
    except Exception as e:
        logging.info("Handling exception in encryption api preparation 1")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return data


@app.task(bind=True)
def prepare_encryption2(self, transfer_output, input_data):
    logging.info("Starting preparation for encryption api 2")
    try:
        data = staging_api.prepare_encryption2(transfer_output, input_data)
    except Exception as e:
        logging.info("Handling exception in encryption api preparation 2")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return data


@app.task(bind=True)
def prepare_encryption3(self, transfer_output, input_data):
    logging.info("Starting preparation for encryption api 3")
    try:
        data = staging_api.prepare_encryption3(transfer_output, input_data)
    except Exception as e:
        logging.info("Handling exception in encryption api preparation 3")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return data


@app.task(bind=True)
def move_nfs(self, input_data, revoke_token=False):
    logging.info("Starting move nfs operation")
    try:
        transfer = staging_api.move_nfs(input_data, revoke_token)
    except Exception as e:
        logging.info("Handling exception in move nfs")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return [app.current_task.request.id, transfer]


@app.task(bind=True)
def prepare_encryption4(self, transfer_output, input_data):
    logging.info("Starting prepare input to iRODS")
    try:
        sys.stdout.write(
            str(staging_api.prepare_input_to_iRODS2(transfer_output, input_data)))
    except Exception as e:
        logging.info("Handling exception in preparing input to iRODS")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return staging_api.prepare_input_to_iRODS2(transfer_output, input_data)


@app.task(bind=True)
def prepare_encryption5(self, transfer_output, input_data):
    logging.info("Starting preparation for encryption api 5")
    try:
        data = staging_api.prepare_encryption5(transfer_output, input_data)
    except Exception as e:
        logging.info("Handling exception in encryption api preparation 5")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
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
    return data


@app.task(bind=True)
def duplicate(self, input_data):
    logging.info("Starting duplication")
    try:
        # duplication function
        transfer = staging_api.duplicate(input_data)
    except Exception as e:
        logging.info("Handling exception in duplication")
        logging.info("Dumping input data")
        logging.info(input_data)
        self.update_state(
            state=states.FAILURE,
            meta={
                'custom': str(e),
                'exc_type': type(e).__name__,
                'exc_message': str(e)})
        logging.info(str(self.AsyncResult(self.request.id).state))
        raise Ignore()
    return [app.current_task.request.id, transfer]
