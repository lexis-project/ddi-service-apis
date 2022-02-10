from django.http import HttpResponse


def NoAuth():
    return HttpResponse(
        '{"status": "401", "errorString": "No Authorization header or wrong format"}',
        content_type='application/json',
        status=401)


def AuthURL():
    return HttpResponse(
        '{"status": "401", "errorString": "Token not accepted by irods: token not valid or not validated by broker. '
        'Or user unknown to iRODS (Auth URL sent by irods)"}',
        content_type='application/json',
        status=401)


def E403():
    return HttpResponse(
        '{"status": "403", "errorString": "User not authorized to perform action"}',
        content_type='application/json',
        status=403)


def E405():
    return HttpResponse(
        '{"status": "405", "errorString": "Method Not Allowed"}',
        content_type='application/json',
        status=405)


def E501():
    return HttpResponse(
        '{"status": "501", "errorString": "Not Implemented, please use JSON API"}',
        content_type='application/json',
        status=501)


def S201():
    return HttpResponse('{"status": "201", "errorString": "Created"}',
                        content_type='application/json', status=201)


def MalformedRequest(text=""):
    return HttpResponse(
        '{"status": "400", "errorString": "Malformed request. %s"}' %
        text, content_type='application/json', status=400)
