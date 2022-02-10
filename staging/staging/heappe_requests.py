import requests
import json
import sys

with open("/etc/staging_api/heappe.json") as file:
    info = json.load(file)


def heappe_auth_keycloack(token, username, heappe_url):
    data = {'Credentials': {}}
    data['Credentials']['Username'] = username
    data['Credentials']['OpenIdAccessToken'] = token
    sys.stdout.write(str(data))
    request_url = heappe_url + "/heappe/UserAndLimitationManagement/AuthenticateUserOpenId"
    r = requests.post(
        request_url, data=json.dumps(
            data, separators=(
                ',', ':')), headers={
            "Content-Type": "application/json"})
    if r.status_code == 200:
        result = {"id": str(r.content.decode("utf-8"))}
        return result
    else:
        return {'error': r.content.decode("utf-8")}


def get_heappe_job(session_code, cluster_id, heappe_url):
    data = info['jobCreation']
    data['sessionCode'] = session_code
    data['ClusterId'] = cluster_id
    sys.stdout.write(str(data))
    request_url = heappe_url + "/heappe/JobManagement/CreateJob"
    r = requests.post(
        request_url, data=json.dumps(
            data, separators=(
                ',', ':')), headers={
            "Content-Type": "application/json"})
    if r.status_code == 200:
        response_string = r.content.decode("utf-8")
        response = json.loads(response_string)
        return {'id': response['Id']}
    else:
        return {'error': r.content.decode("utf-8")}


def get_heappe_file_transfer(session_code, job_id, heappe_url):
    data = {"submittedJobInfoId": job_id, "sessionCode": str(session_code)}
    sys.stdout.write(str(data))
    request_url = heappe_url + "/heappe/FileTransfer/GetFileTransferMethod"
    r = requests.post(request_url, data=json.dumps(data),
                      headers={"Content-Type": "application/json"})
    if r.status_code == 200:
        return {"Access": r.content.decode("utf-8")}
    else:
        return {"error": r.content.decode("utf-8")}


def end_heappe_file_transfer(
        session_code,
        file_transfer_data,
        job_id,
        heappe_url):
    input_data = file_transfer_data['Access']
    input_data = json.loads(input_data)
    sys.stdout.write(str(input_data))
    data = {'submittedJobInfoId': job_id, 'usedTransferMethod': {}}
    data['usedTransferMethod']['ServerHostname'] = input_data['ServerHostname']
    data['usedTransferMethod']['SharedBasepath'] = input_data['SharedBasepath']
    data['usedTransferMethod']['Protocol'] = input_data['Protocol']
    data['usedTransferMethod']['Credentials'] = {}
    data['usedTransferMethod']['Credentials']['Username'] = input_data['Credentials']['Username']
    data['usedTransferMethod']['Credentials']['PublicKey'] = input_data['Credentials']['PublicKey']
    data['usedTransferMethod']['Credentials']['PrivateKey'] = input_data['Credentials']['PrivateKey']
    data['sessionCode'] = session_code
    sys.stdout.write(str(data))
    request_url = heappe_url + "/heappe/FileTransfer/EndFileTransfer"
    r = requests.post(request_url, data=json.dumps(data),
                      headers={"Content-Type": "application/json"})
    if r.status_code == 200:
        return {'status': r.content.decode("utf-8")}
    else:
        return {'error': r.content.decode("utf-8")}
