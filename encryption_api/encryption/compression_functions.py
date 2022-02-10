import subprocess
import os
import uuid
import shutil
import yaml
import sys

with open("/etc/staging_api/system.yml") as file:
    input_data = yaml.load(file, Loader=yaml.FullLoader)
    systems = input_data["systems"]


def compress_data(path_to_data, move=True):
    if os.path.isdir(path_to_data):
        dataset = os.path.basename(path_to_data)
        temp_area = input_data["local_staging_area"]
        temp_base_path = systems[temp_area]["base_path"]
        if move:
            temp_dir = temp_base_path + str(uuid.uuid1())
            temp_dataset = temp_dir + "/" + dataset
            shutil.move(path_to_data, temp_dataset)
        else:
            temp_dir = os.path.abspath(os.path.join(path_to_data, os.pardir))
            temp_dataset = path_to_data
        os.chdir(temp_dir)
        output = dataset + ".tar.gz"
        final_output = temp_dir + "/" + output
        command = "tar c " + dataset + " | pigz -c -k > " + output
        sys.stdout.write(command)
        popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        while True:
            popen.stdout.read(1)
            if popen.poll() is not None:
                sys.stdout.write("Finished zipping")
                break
        popen.wait()
        if popen.returncode != 0:
            sys.stdout.write("Problem creating zip files")
    else:
        raise FileNotFoundError("Dataset not found")
    if os.path.isfile(output):
        return final_output
    else:
        raise Exception("Something went wrong with compression")


def decompress_data(path_to_data, move=True):
    if os.path.isfile(path_to_data):
        dataset = os.path.basename(path_to_data)
        temp_area = input_data["local_staging_area"]
        temp_base_path = systems[temp_area]["base_path"]
        if move:
            temp_dir = temp_base_path + str(uuid.uuid1())
            os.mkdir(temp_dir)
            shutil.move(path_to_data, temp_dir)
        else:
            temp_dir = os.path.abspath(os.path.join(path_to_data, os.pardir))
        os.chdir(temp_dir)
        output = str(uuid.uuid1())
        os.mkdir(output)
        final_output = temp_dir + "/" + output
        command = "tar -I pigz -xvf " + dataset + " -C " + output
        sys.stdout.write(command)
        popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        while True:
            popen.stdout.read(1)
            if popen.poll() is not None:
                sys.stdout.write("Finished unzipping")
                break
        popen.wait()
        if popen.returncode != 0:
            sys.stdout.write("Problem creating zip files")
    else:
        raise FileNotFoundError("Dataset not found")
    if os.path.isdir(output):
        return final_output
    else:
        raise Exception("Something went wrong with compression")
