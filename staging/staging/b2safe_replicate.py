import sys
import jwt
import textwrap
import time
import os
from irods.session import iRODSSession
from irods.rule import Rule
import irods.exception as iRODSExceptions
from . import irods_transfer

tmp_path = "/etc/staging_api/tmp/"


def get_user(token):
    sys.stdout.write(token)
    dec = jwt.decode(token.encode('utf-8'), verify=False)
    user = dec.get('irods_name', dec.get('preferred_username'))
    sys.stdout.write(user)
    return user


def get_session(token, system_info):
    user = get_user(token)
    session = iRODSSession(
        host=system_info.get('host'),
        port=system_info.get('port'),
        authentication_scheme='openid',
        openid_provider='keycloak_openid',
        zone=system_info.get('zone'),
        access_token=token,
        user=user,
        block_on_authURL=False)
    return session


def replicate(session, source, destination):
    try:
        coll_source = session.collections.get(source)
        sys.stdout.write(destination)
        sys.stdout.write("Replication will start")
        ts = time.time()
        rule_file_path = (tmp_path + "eudatRepl_{ts}.r").format(**locals())
        rule = textwrap.dedent('''\
                        eudatRepl {{
                            EUDATReplication(*source, *destination, "true", "false", *response)
                                  }}
                        INPUT *source="{source}", *destination="{destination}"
                        OUTPUT *response, ruleExecOut'''.format(**locals()))

        with open(rule_file_path, "w") as rule_file:
            rule_file.write(rule)
        myrule = Rule(session, rule_file_path)
        rule_result = myrule.execute()
        sys.stdout.write(str(rule_result))
        os.remove(rule_file_path)
    except iRODSExceptions.CollectionDoesNotExist:
        raise (
            Exception("The collection that you are trying to replicate doesn't exist"))
    try:
        coll_destination = session.collections.get(destination)
        pid = coll_destination.metadata.get_one("PID")
        size_input = irods_transfer.coll_size(session, source)
        size_output = irods_transfer.coll_size(session, destination)
        sys.stdout.write(str(size_input))
        sys.stdout.write(str(size_output))
        for meta in coll_source.metadata.items():
            try:
                if "EUDAT" not in meta.name and "PID" not in meta.name:
                    coll_destination.metadata.add(
                        str(meta.name), str(meta.value))
            except BaseException:
                raise (Exception("Couldn't set metadata in target directory"))
        if size_input == size_output:
            return [destination, str(pid.value)]
        else:
            raise (Exception(
                "Dataset wasn't replicated sucessfully. Source size doesn't match destination size"))
    except iRODSExceptions.CollectionDoesNotExist:
        sys.stdout.write("Destination doesn't exist")
        raise (Exception("Dataset wasn't replicated sucessfully"))


def assign_pid(session, source, parent_pid=None):
    parent_pid = str(parent_pid)
    try:
        coll_source = session.collections.get(source)
        ts = time.time()
        rule_file_path = (tmp_path + "eudatPidsColl_{ts}.r").format(**locals())
        rule = textwrap.dedent('''\
                        eudatPidsColl {{
                            EUDATCreatePID(*parent_pid, *source, "None", "None", "true", *newPID)
                                  }}
                            INPUT *parent_pid="{parent_pid}", *source="{source}"
                            OUTPUT *newPID, ruleExecOut'''.format(**locals()))

        with open(rule_file_path, "w") as rule_file:
            rule_file.write(rule)
        myrule = Rule(session, rule_file_path)
        sys.stdout.write(str(myrule.execute()))
        os.remove(rule_file_path)
    except iRODSExceptions.CollectionDoesNotExist:
        raise (Exception(
            "The collection that you are trying to assign a PID for doesn't exist"))
    try:
        pid = coll_source.metadata.get_one("PID")
        return str(pid.value)
    except KeyError:
        raise (Exception("Something went wrong with PID assignment"))
