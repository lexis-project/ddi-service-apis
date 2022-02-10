import hashlib

def hash(project_name):
    return "proj" + hashlib.md5(project_name.encode()).hexdigest()
