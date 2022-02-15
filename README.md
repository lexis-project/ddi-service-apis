# ddi-service-apis

<a href="https://doi.org/10.5281/zenodo.6046596"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.6046596.svg" alt="DOI"></a>

LEXIS DDI APIs, e.g. for data staging between iRODS and different computing systems.

The LEXIS DDI API are implemented in Python Django, separated to five standalone Django applications. Ansible roles are included in the [ansible](ansible) directory in the repo.

## Acknowledgement
This code repository is a result / contains results of the LEXIS project. The project has received funding from the European Union’s Horizon 2020 Research and Innovation programme (2014-2020) under grant agreement No. 825532.

## Components
The DDI uses modified iRODS client for Python forked here: [https://github.com/lexis-project/python-irodsclient](https://github.com/lexis-project/python-irodsclient).

### iRODS API
Implements the CRUD operations for datasets and their metadata, users, projects. This API is also used to provide download/upload capabilities through calls to the Staging API. Python Django is used as REST API frontend and uses library located at [irodsapi/irodsApisForWp8](irodsapi/irodsApisForWp8).

### Staging API 
This module implements operations for moving the data between different centres and storage resources, querying data size and othe information which is not stored in the dataset metadata.

### SSHFS export API
This module provides operations for exposing a POSIX path via SFTP/SCP with an explicit public key. This is used mainly to mount large datasets to cloud instances.

## Ansible Roles
Each module has its own role located in the [ansible](ansible) directory, the roles use the general roles django, celery and uwsgi. The general roles are not meant to be used directly. The main playbook.yml contains the mapping between the inventory and the roles.

Variables are documented in [ansible/group_vars/all.yml](all.yml) file.

### Django
Deploys a Django app in a Python package built using setuptools sdist. 

### uwsgi
Deploys and configures UWSGI in Emperor mode for both Debian and Centos.

### Celery
Deploys Celery systemd unit, expects celery and celery app to be deployed using the above django role. This role is used to deploy the celery workers of iRODS and Staging API.
