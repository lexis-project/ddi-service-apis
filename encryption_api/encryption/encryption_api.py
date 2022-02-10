import yaml
import os
import base64
from . import compression_functions
from . import encryption_functions

with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)
    encryption = systems["encryption"]


def get_passphrase(secrets_list, project):
    res = next((sub for sub in secrets_list if sub['PRJ'] == project), None)
    passphrase = res["PASSPHRASE"]
    base64_bytes = passphrase.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    return message


def encrypt(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    secrets = input_data["secrets"]
    project = input_data["project"]
    passphrase = get_passphrase(secrets, project)
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    if os.path.isdir(source_path_complete):
        encryption_call = encryption_functions.encrypt_data(
            source_path_complete, passphrase)
    else:
        encryption_call = encryption_functions.encrypt_file(
            source_path_complete, passphrase)
    return encryption_call


def decrypt(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    secrets = input_data["secrets"]
    project = input_data["project"]
    passphrase = get_passphrase(secrets, project)
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    if os.path.isdir(source_path_complete):
        decryption = encryption_functions.decrypt_data(
            source_path_complete, passphrase)
    else:
        decryption = encryption_functions.decrypt_file(
            source_path_complete, passphrase)
    return decryption


def compress(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    compression = compression_functions.compress_data(source_path_complete)
    return compression


def decompress(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    decompression = compression_functions.decompress_data(source_path_complete)
    return decompression


def compress_encryt(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    secrets = input_data["secrets"]
    project = input_data["project"]
    passphrase = get_passphrase(secrets, project)
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    compression = compression_functions.compress_data(source_path_complete)
    encryption_call = encryption_functions.encrypt_file(
        compression, passphrase, move=False)
    return encryption_call


def decrypt_decompress(input_data):
    source_system = input_data["source_system"]
    source_path = input_data["source_path"]
    secrets = input_data["secrets"]
    project = input_data["project"]
    passphrase = get_passphrase(secrets, project)
    source_info = systems["systems"][source_system]
    source_path_complete = source_info.get("base_path") + source_path
    if os.path.isdir(source_path_complete):
        decryption = encryption_functions.decrypt_data(
            source_path_complete, passphrase)
    else:
        decryption = encryption_functions.decrypt_file(
            source_path_complete, passphrase)
    decompression = compression_functions.decompress_data(
        decryption, move=False)
    return decompression
