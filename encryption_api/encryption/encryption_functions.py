import subprocess
import os
import uuid
import shutil
import yaml
import sys

with open("/etc/staging_api/system.yml") as file:
    input_data = yaml.load(file, Loader=yaml.FullLoader)
    systems = input_data["systems"]
    encryption = input_data["encryption"]


def encrypt_data(path_to_data, passphrase, move=True):
    if os.path.isdir(path_to_data):
        dataset = os.path.basename(path_to_data)
        temp_area = input_data["burst_buffer_area"]
        temp_base_path = systems[temp_area]["base_path"]
        if move:
            temp_dir = temp_base_path + str(uuid.uuid1())
            temp_dataset = temp_dir + "/" + dataset
            shutil.move(path_to_data, temp_dataset)
        else:
            temp_dir = os.path.abspath(os.path.join(path_to_data, os.pardir))
            temp_dataset = path_to_data
        enc_mod = encryption["enc_mod"]
        hash_md = encryption["hash_md"]
        openssl_key_deriv = encryption["openssl_key_deriv"]
        openssl_path = encryption["openssl_path"]
        output = dataset + "_enc"
        final_output = temp_dir + "/" + output
        os.mkdir(final_output)
        for subdir, dirs, files in os.walk(temp_dataset):
            for dir_call in dirs:
                full_path = os.path.join(subdir, dir_call)
                abs_path = full_path.replace(temp_dataset, '')
                target_dir = final_output + abs_path
                os.mkdir(target_dir)
            for filename in files:
                file_enc = os.path.join(subdir, filename)
                abs_file = file_enc.replace(temp_dataset, '')
                obj = final_output + abs_file
                command = openssl_path + "openssl enc -e -" + enc_mod + " -a -salt -p -md " + \
                          hash_md + " " + openssl_key_deriv + " -in " + file_enc + " -out " + obj + " -pass stdin"
                sys.stdout.write(command + "\n")
                popen = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE)
                popen.stdin.write(passphrase.encode('utf-8'))
                popen.stdin.close()
                while True:
                    popen.stdout.read(1)
                    if popen.poll() is not None:
                        sys.stdout.write("Finished encrypting:" + file_enc)
                        break
                popen.wait()
                if popen.returncode != 0:
                    sys.stdout.write("Problem creating zip files: " + file_enc)
    else:
        raise FileNotFoundError("Dataset not found")
    if os.path.isdir(final_output):
        return final_output
    else:
        raise Exception("Something went wrong with compression")


def encrypt_file(path_to_data, passphrase, move=True):
    if os.path.isfile(path_to_data):
        dataset = os.path.basename(path_to_data)
        temp_area = input_data["burst_buffer_area"]
        temp_base_path = systems[temp_area]["base_path"]
        if move:
            temp_dir = temp_base_path + str(uuid.uuid1())
            os.mkdir(temp_dir)
            temp_dataset = temp_dir + "/" + dataset
            shutil.move(path_to_data, temp_dataset)
        else:
            temp_dir = os.path.abspath(os.path.join(path_to_data, os.pardir))
            temp_dataset = path_to_data
        enc_mod = encryption["enc_mod"]
        hash_md = encryption["hash_md"]
        openssl_key_deriv = encryption["openssl_key_deriv"]
        openssl_path = encryption["openssl_path"]
        output = "enc_" + dataset
        final_output = temp_dir + "/" + output
        command = openssl_path + "openssl enc -e -" + enc_mod + " -a -salt -p -md " + hash_md + \
            " " + openssl_key_deriv + " -in " + temp_dataset + " -out " + final_output + " -pass stdin"
        sys.stdout.write(command + "\n")
        popen = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE)
        popen.stdin.write(passphrase.encode('utf-8'))
        popen.stdin.close()
        while True:
            popen.stdout.read(1)
            if popen.poll() is not None:
                sys.stdout.write("Finished encrypting:" + dataset)
                break
            popen.wait()
            if popen.returncode != 0:
                sys.stdout.write("Problem creating zip files: " + dataset)
    else:
        raise FileNotFoundError("Dataset not found")
    if os.path.isfile(final_output):
        return final_output
    else:
        raise Exception("Something went wrong with compression")


def decrypt_data(path_to_data, passphrase, move=True):
    if os.path.isdir(path_to_data):
        dataset = os.path.basename(path_to_data)
        temp_area = input_data["burst_buffer_area"]
        temp_base_path = systems[temp_area]["base_path"]
        if move:
            temp_dir = temp_base_path + str(uuid.uuid1())
            temp_dataset = temp_dir + "/" + dataset
            shutil.move(path_to_data, temp_dataset)
        else:
            temp_dir = os.path.abspath(os.path.join(path_to_data, os.pardir))
            temp_dataset = path_to_data
        enc_mod = encryption["enc_mod"]
        hash_md = encryption["hash_md"]
        openssl_path = encryption["openssl_path"]
        openssl_key_deriv = encryption["openssl_key_deriv"]
        output = dataset + "_dec"
        final_output = temp_dir + "/" + output
        os.mkdir(final_output)
        for subdir, dirs, files in os.walk(temp_dataset):
            for dir_call in dirs:
                full_path = os.path.join(subdir, dir_call)
                abs_path = full_path.replace(temp_dataset, '')
                target_dir = final_output + abs_path
                os.mkdir(target_dir)
            for filename in files:
                file_enc = os.path.join(subdir, filename)
                abs_file = file_enc.replace(temp_dataset, '')
                obj = final_output + abs_file
                command = openssl_path + "openssl enc -d -" + enc_mod + " -a -salt -p -md " + \
                          hash_md + " " + openssl_key_deriv + " -in " + file_enc + " -out " + obj + " -pass stdin"
                sys.stdout.write(command + "\n")
                popen = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE)
                popen.stdin.write(passphrase.encode('utf-8'))
                popen.stdin.close()
                while True:
                    popen.stdout.read(1)
                    if popen.poll() is not None:
                        sys.stdout.write("Finished encrypting:" + file_enc)
                        break
                popen.wait()
                if popen.returncode != 0:
                    sys.stdout.write("Problem creating zip files: " + file_enc)
    else:
        raise FileNotFoundError("Dataset not found")
    if os.path.isdir(final_output):
        return final_output
    else:
        raise Exception("Something went wrong with compression")


def decrypt_file(path_to_data, passphrase, move=True):
    if os.path.isfile(path_to_data):
        dataset = os.path.basename(path_to_data)
        temp_area = input_data["burst_buffer_area"]
        temp_base_path = systems[temp_area]["base_path"]
        if move:
            temp_dir = temp_base_path + str(uuid.uuid1())
            os.mkdir(temp_dir)
            temp_dataset = temp_dir + "/" + dataset
            shutil.move(path_to_data, temp_dataset)
        else:
            temp_dir = os.path.abspath(os.path.join(path_to_data, os.pardir))
            temp_dataset = path_to_data
        enc_mod = encryption["enc_mod"]
        hash_md = encryption["hash_md"]
        openssl_key_deriv = encryption["openssl_key_deriv"]
        openssl_path = encryption["openssl_path"]
        output = "dec_" + dataset
        final_output = temp_dir + "/" + output
        command = openssl_path + "openssl enc -d -" + enc_mod + " -a -salt -p -md " + hash_md + \
            " " + openssl_key_deriv + " -in " + temp_dataset + " -out " + final_output + " -pass stdin"
        sys.stdout.write(command + "\n")
        popen = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE)
        popen.stdin.write(passphrase.encode('utf-8'))
        popen.stdin.close()
        while True:
            popen.stdout.read(1)
            if popen.poll() is not None:
                sys.stdout.write("Finished encrypting:" + dataset)
                break
            popen.wait()
            if popen.returncode != 0:
                sys.stdout.write("Problem creating zip files: " + dataset)
    else:
        raise FileNotFoundError("Dataset not found")
    if os.path.isfile(final_output):
        return final_output
    else:
        raise Exception("Something went wrong with compression")
