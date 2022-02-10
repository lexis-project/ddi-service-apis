from . import generate_config
from . import tasks
from . import staging_api
import encryption.tasks
import celery
import sys


def trigger_staging_task(input_data):
    source_location = generate_config.get_location(input_data["source_system"])
    target_location = generate_config.get_location(input_data["target_system"])
    target_bb_location = target_location + "_bb"
    source_bb_location = source_location + "_bb"
    source_type = generate_config.get_type(input_data["source_system"])
    target_type = generate_config.get_type(input_data["target_system"])
    staging_queue = generate_config.get_category(
        source_location, target_location)
    staging_class = generate_config.get_class(
        source_type, source_location, target_type, target_location)
    bb_queue = generate_config.get_bb_queue()
    revoke_token = True
    if staging_queue == "Z" or staging_queue == "federation":
        raise "Source and target combination is not supported"
    if staging_class == 1:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            staging = tasks.stage_class_1.s(
                input_data, revoke_token=revoke_token).set(queue=staging_queue)
            res = staging.apply_async()
        else:
            project = staging_api.get_project_from_source(input_data)
            input_data["project"] = project
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_1.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption3.s(
                input_data).set(queue=staging_queue)
            transfer2 = tasks.move_nfs.s(revoke_token).set(queue=staging_queue)
            if (input_data["encryption"] ==
                    "yes" and input_data["compression"] == "no"):
                encrypt = encryption.tasks.decrypt.s().set(queue=target_bb_location)
            elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
                encrypt = encryption.tasks.decompress.s().set(queue=target_bb_location)
            else:
                encrypt = encryption.tasks.decrypt_decompress.s().set(queue=target_bb_location)
            res = celery.chain(
                preprocessing1,
                transfer1,
                preprocessing2,
                encrypt,
                preprocessing3,
                transfer2)()
    elif staging_class == 2:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            staging = tasks.stage_class_2.s(
                input_data, revoke_token=revoke_token).set(queue=staging_queue)
            res = staging.apply_async()
        else:
            project = staging_api.get_project_from_target(input_data)
            input_data["project"] = project
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_3.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption3.s(
                input_data).set(queue=staging_queue)
            clean_source = True
            transfer2 = tasks.stage_class_2.s(
                clean_source, revoke_token).set(queue=staging_queue)
            if (input_data["encryption"] ==
                    "yes" and input_data["compression"] == "no"):
                encrypt = encryption.tasks.encrypt.s().set(queue=source_bb_location)
            elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
                encrypt = encryption.tasks.compress.s().set(queue=source_bb_location)
            else:
                encrypt = encryption.tasks.compress_encrypt.s().set(queue=source_bb_location)
            res = celery.chain(
                preprocessing1,
                transfer1,
                preprocessing2,
                encrypt,
                preprocessing3,
                transfer2)()
    elif staging_class == 3:
        staging = tasks.stage_class_3.s(input_data, revoke_token=revoke_token).set(queue=staging_queue)
        res = staging.apply_async()
    elif staging_class == 4:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            staging = tasks.stage_class_4.s(
                input_data, revoke_token=revoke_token).set(queue=staging_queue)
            res = staging.apply_async()
        else:
            project = staging_api.get_project_from_source(input_data)
            input_data["project"] = project
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_1.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption3.s(
                input_data).set(queue=staging_queue)
            clean_source = True
            transfer2 = tasks.stage_class_6.s(
                clean_source, revoke_token).set(queue=staging_queue)
            if (input_data["encryption"] ==
                    "yes" and input_data["compression"] == "no"):
                encrypt = encryption.tasks.decrypt.s().set(queue=target_bb_location)
            elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
                encrypt = encryption.tasks.decompress.s().set(queue=target_bb_location)
            else:
                encrypt = encryption.tasks.decrypt_decompress.s().set(queue=target_bb_location)
            res = celery.chain(
                preprocessing1,
                transfer1,
                preprocessing2,
                encrypt,
                preprocessing3,
                transfer2)()
    elif staging_class == 5:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            staging = tasks.stage_class_5.s(
                input_data, revoke_token=revoke_token).set(queue=staging_queue)
            res = staging.apply_async()
        else:
            project = staging_api.get_project_from_target(input_data)
            input_data["project"] = project
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_7.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption3.s(
                input_data).set(queue=staging_queue)
            clean_source = True
            transfer2 = tasks.stage_class_2.s(
                clean_source, revoke_token).set(queue=staging_queue)
            if (input_data["encryption"] ==
                    "yes" and input_data["compression"] == "no"):
                encrypt = encryption.tasks.encrypt.s().set(queue=source_bb_location)
            elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
                encrypt = encryption.tasks.compress.s().set(queue=source_bb_location)
            else:
                encrypt = encryption.tasks.compress_encrypt.s().set(queue=source_bb_location)
            res = celery.chain(
                preprocessing1,
                transfer1,
                preprocessing2,
                encrypt,
                preprocessing3,
                transfer2)()
    elif staging_class == 6:
        staging = tasks.stage_class_6.s(input_data, revoke_token=revoke_token).set(queue=staging_queue)
        res = staging.apply_async()
    elif staging_class == 7:
        staging = tasks.stage_class_7.s(input_data, revoke_token=revoke_token).set(queue=staging_queue)
        res = staging.apply_async()
    elif staging_class == 8:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            preprocessing = tasks.preprocess_input.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_2.s().set(queue=staging_queue)
            postprocessing = tasks.postprocess_input.s(
                input_data).set(queue=staging_queue)
            transfer2 = tasks.stage_class_4.s(revoke_token=revoke_token).set(queue=target_location)
            res = celery.chain(
                preprocessing,
                transfer1,
                postprocessing,
                transfer2)()
        else:
            new_secrets = staging_api.get_random_key_and_apppend(
                input_data["secrets"])
            input_data["project"] = "user"
            input_data["secrets"] = new_secrets
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_3.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption4.s(
                input_data).set(queue=staging_queue)
            clean_source = True
            transfer2 = tasks.stage_class_2.s(
                clean_source).set(queue=staging_queue)
            preprocessing4 = tasks.prepare_encryption5.s(
                input_data).set(queue=target_location)
            transfer3 = tasks.stage_class_1.s(
                clean_source).set(queue=target_location)
            preprocessing5 = tasks.prepare_encryption2.s(
                input_data).set(queue=target_location)
            preprocessing6 = tasks.prepare_encryption3.s(
                input_data).set(queue=target_location)
            transfer4 = tasks.stage_class_6.s(
                clean_source, revoke_token).set(queue=target_location)
            if (input_data["encryption"] ==
                    "yes" and input_data["compression"] == "no"):
                encrypt = encryption.tasks.encrypt.s().set(queue=source_bb_location)
                decrypt = encryption.tasks.decrypt.s().set(queue=target_bb_location)
            elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
                encrypt = encryption.tasks.compress.s().set(queue=source_bb_location)
                decrypt = encryption.tasks.decompress.s().set(queue=target_bb_location)
            else:
                encrypt = encryption.tasks.compress_encrypt.s().set(queue=source_bb_location)
                decrypt = encryption.tasks.decrypt_decompress.s().set(queue=target_bb_location)
            res = celery.chain(
                preprocessing1,
                transfer1,
                preprocessing2,
                encrypt,
                preprocessing3,
                transfer2,
                preprocessing4,
                transfer3,
                preprocessing5,
                decrypt,
                preprocessing6,
                transfer4)()
    elif staging_class == 9:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            preprocessing = tasks.preprocess_input.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_5.s().set(queue=staging_queue)
            postprocessing = tasks.postprocess_input.s(
                input_data).set(queue=staging_queue)
            transfer2 = tasks.stage_class_1.s(revoke_token=revoke_token).set(queue=target_location)
            res = celery.chain(
                preprocessing,
                transfer1,
                postprocessing,
                transfer2)()
            sys.stdout.write(str(res))
        else:
            new_secrets = staging_api.get_random_key_and_apppend(
                input_data["secrets"])
            input_data["project"] = "user"
            input_data["secrets"] = new_secrets
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_7.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption4.s(
                input_data).set(queue=staging_queue)
            clean_source = True
            transfer2 = tasks.stage_class_2.s(
                clean_source).set(queue=staging_queue)
            preprocessing4 = tasks.prepare_encryption5.s(
                input_data).set(queue=target_location)
            transfer3 = tasks.stage_class_1.s(
                clean_source).set(queue=target_location)
            preprocessing5 = tasks.prepare_encryption2.s(
                input_data).set(queue=target_location)
            preprocessing6 = tasks.prepare_encryption3.s(
                input_data).set(queue=target_location)
            transfer4 = tasks.move_nfs.s(revoke_token).set(queue=target_location)
            if (input_data["encryption"] ==
                    "yes" and input_data["compression"] == "no"):
                encrypt = encryption.tasks.encrypt.s().set(queue=source_bb_location)
                decrypt = encryption.tasks.decrypt.s().set(queue=target_bb_location)
            elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
                encrypt = encryption.tasks.compress.s().set(queue=source_bb_location)
                decrypt = encryption.tasks.decompress.s().set(queue=target_bb_location)
            else:
                encrypt = encryption.tasks.compress_encrypt.s().set(queue=source_bb_location)
                decrypt = encryption.tasks.decrypt_decompress.s().set(queue=target_bb_location)
            res = celery.chain(
                preprocessing1,
                transfer1,
                preprocessing2,
                encrypt,
                preprocessing3,
                transfer2,
                preprocessing4,
                transfer3,
                preprocessing5,
                decrypt,
                preprocessing6,
                transfer4)()
    elif staging_class == 10:
        if(input_data["encryption"] == "no" and input_data["compression"] == "no"):
            preprocessing = tasks.preprocess_input.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_2.s().set(queue=staging_queue)
            postprocessing = tasks.postprocess_input.s(
                input_data).set(queue=staging_queue)
            transfer2 = tasks.stage_class_1.s(revoke_token=revoke_token).set(queue=target_location)
            res = celery.chain(
                preprocessing,
                transfer1,
                postprocessing,
                transfer2)()
        else:
            new_secrets = staging_api.get_random_key_and_apppend(
                input_data["secrets"])
            input_data["project"] = "user"
            input_data["secrets"] = new_secrets
            preprocessing1 = tasks.prepare_encryption1.s(
                input_data).set(queue=staging_queue)
            transfer1 = tasks.stage_class_3.s().set(queue=staging_queue)
            preprocessing2 = tasks.prepare_encryption2.s(
                input_data).set(queue=staging_queue)
            preprocessing3 = tasks.prepare_encryption4.s(
                input_data).set(queue=staging_queue)
            clean_source = True
            transfer2 = tasks.stage_class_2.s(
                clean_source).set(queue=staging_queue)
            preprocessing4 = tasks.prepare_encryption5.s(
                input_data).set(queue=target_location)
            transfer3 = tasks.stage_class_1.s(
                clean_source).set(queue=target_location)
            preprocessing5 = tasks.prepare_encryption2.s(
                input_data).set(queue=target_location)
            preprocessing6 = tasks.prepare_encryption3.s(
                input_data).set(queue=target_location)
            transfer4 = tasks.move_nfs.s(revoke_token).set(queue=target_location)
        if (input_data["encryption"] ==
                "yes" and input_data["compression"] == "no"):
            encrypt = encryption.tasks.encrypt.s().set(queue=source_bb_location)
            decrypt = encryption.tasks.decrypt.s().set(queue=target_bb_location)
        elif (input_data["encryption"] == "no" and input_data["compression"] == "yes"):
            encrypt = encryption.tasks.compress.s().set(queue=source_bb_location)
            decrypt = encryption.tasks.decompress.s().set(queue=target_bb_location)
        else:
            encrypt = encryption.tasks.compress_encrypt.s().set(queue=source_bb_location)
            decrypt = encryption.tasks.decrypt_decompress.s().set(queue=target_bb_location)
        res = celery.chain(
            preprocessing1,
            transfer1,
            preprocessing2,
            encrypt,
            preprocessing3,
            transfer2,
            preprocessing4,
            transfer3,
            preprocessing5,
            decrypt,
            preprocessing6,
            transfer4)()
    return res


def trigger_deletion_task(input_data):
    target_type = generate_config.get_type(input_data["target_system"])
    staging_queue = generate_config.get_location(input_data["target_system"])
    if staging_queue == "federation":
        staging_queue = generate_config.get_local_queue()
    sys.stdout.write(staging_queue)
    deletion_class = generate_config.get_deletion_class(target_type)
    if deletion_class == "del_1":
        deletion = tasks.delete_class_1.s(input_data).set(queue=staging_queue)
    elif deletion_class == "del_2":
        deletion = tasks.delete_class_2.s(input_data).set(queue=staging_queue)
    elif deletion_class == "del_3":
        deletion = tasks.delete_class_3.s(input_data).set(queue=staging_queue)
    res = deletion.apply_async()
    return res


def trigger_get_data_size(input_data):
    staging_queue = generate_config.get_local_queue()
    size = tasks.get_data_size.s(input_data).set(queue=staging_queue)
    res = size.apply_async()
    return res


def trigger_replication(input_data):
    staging_queue = generate_config.get_local_queue()
    replication = tasks.replicate.s(input_data).set(queue=staging_queue)
    res = replication.apply_async()
    return res


def trigger_pid_assignment(input_data):
    staging_queue = generate_config.get_local_queue()
    pid = tasks.assign_pid.s(input_data).set(queue=staging_queue)
    res = pid.apply_async()
    return res


def trigger_duplication(input_data):
    staging_queue = generate_config.get_local_queue()
    duplicate = tasks.duplicate.s(input_data).set(queue=staging_queue)
    res = duplicate.apply_async()
    return res
