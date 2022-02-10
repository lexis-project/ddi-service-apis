from paramiko import SSHClient, SSHException
import paramiko
from scp import SCPClient
import io
import os
import sys
from scp import SCPException
from socket import error as SocketError, timeout as SocketTimeout


def transform_key(private_key):
    key_value = io.StringIO(private_key)
    private_key_final = paramiko.RSAKey.from_private_key(key_value)
    key_value.close()
    return private_key_final


def remote_cp_to_hpc(source_path, destination_path, ssh_user, ssh_priv_key):
    target_data = destination_path.split(":/")
    ssh = SSHClient()
    private_key = transform_key(ssh_priv_key)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.load_system_host_keys()
    try:
        ssh.connect(
            hostname=target_data[0],
            username=ssh_user,
            pkey=private_key)
        with SCPClient(ssh.get_transport(), socket_timeout=60) as scp:
            if os.path.isdir(source_path):
                sys.stdout.write("it is a dir")
                for file in os.listdir(source_path):
                    sub_dir = os.path.join(source_path, file)
                    scp.put(
                        sub_dir,
                        recursive=True,
                        remote_path=target_data[1])
            else:
                scp.put(
                    source_path,
                    recursive=False,
                    remote_path=target_data[1])
        ssh.close()
        sys.stdout.write("it worked")
    except SSHException as r:
        sys.stdout.write("fail with: " + str(r))
    except SocketError as v:
        sys.stdout.write("fail with: " + str(v))
    except SocketTimeout as w:
        sys.stdout.write("fail with: " + str(w))
    except SCPException as x:
        sys.stdout.write("fail with" + str(x))


def remote_cp_from_hpc(source_path, destination_path, ssh_user, ssh_priv_key):
    os.chdir(destination_path)
    source_data = source_path.split(":/")
    ssh = SSHClient()
    private_key = transform_key(ssh_priv_key)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.load_system_host_keys()
    try:
        ssh.connect(source_data[0], username=ssh_user, pkey=private_key)
        with SCPClient(ssh.get_transport(), socket_timeout=60) as scp:
            sys.stdout.write(source_data[1])
            scp.get(remote_path=source_data[1], recursive=True)
        ssh.close()
        sys.stdout.write("It worked !!")
    except SSHException as r:
        sys.stdout.write("fail with: " + str(r))
    except SocketError as v:
        sys.stdout.write("fail with: " + str(v))
    except SocketTimeout as w:
        sys.stdout.write("fail with: " + str(w))
    except SCPException as x:
        sys.stdout.write("fail with" + str(x))


def delete_hpc(destination_path, ssh_user, ssh_priv_key):
    target_data = destination_path.split(":/")
    sys.stdout.write(target_data[0])
    sys.stdout.write(target_data[1])
    ssh = SSHClient()
    private_key = transform_key(ssh_priv_key)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    try:
        ssh.connect(
            hostname=target_data[0],
            username=ssh_user,
            pkey=private_key)
        if os.path.isdir(target_data[1]):
            ssh.exec_command("rm -r " + target_data[1])
        else:
            ssh.exec_command("rm " + target_data[1])
        ssh.close()
        sys.stdout.write("It worked !!")
    except SSHException as r:
        sys.stdout.write("fail with: " + str(r))
    except SocketError as v:
        sys.stdout.write("fail with: " + str(v))
    except SocketTimeout as w:
        sys.stdout.write("fail with: " + str(w))
    except SCPException as x:
        sys.stdout.write("fail with" + str(x))
