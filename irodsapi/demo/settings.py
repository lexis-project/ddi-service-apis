#irods configuration
import environ
import json
import os
env = environ.Env(DEBUG=(bool, False))

if 'ENV_PATH' in os.environ:
   env.read_env(env.str('ENV_PATH'))
else:
   env.read_env('/etc/irods_api.conf')


IRODS = {
  'zone': env.str('IRODS_API_IRODS_ZONE', default=''),
  'user': env.str('IRODS_API_IRODS_USER', default=''),
  'host': env.str('IRODS_API_IRODS_HOST', default=''), 
  'port': env.int('IRODS_API_IRODS_PORT', default=1247),
  'openid_microservice': env.str('IRODS_API_IRODS_OPENID_MICROSERVICE', default=''),
  'sslVerification': 'True' == env.bool('IRODS_API_IRODS_SSL_VERIFICATION', default=None),
  'federated': env.list('IRODS_API_IRODS_FEDERATED', default='[""]'),
  'pwd': env.str('IRODS_API_IRODS_PWD', default=''),
}

GLOBUS = {
  'client-id': env.str('IRODS_API_GLOBUS_',  default=''),
  'key': env.str('IRODS_API_GLOBUS_',  default=''),
  'cert': env.str('IRODS_API_GLOBUS_',  default=''),
  'endpoint': env.str('IRODS_API_GLOBUS_',  default=''),
  'path': env.str('IRODS_API_GLOBUS_',  default=''),
  'auth_refresh_token': env.str('IRODS_API_GLOBUS_',  default=''),
  'transfer_refresh_token': env.str('IRODS_API_GLOBUS_',  default=''),
}

STAGING= {
  'path': env.str('IRODS_API_STAGING_PATH',  default=''),
  'internal_path': env.str('IRODS_API_INTERNAL_STAGING_PATH', default=''),
  "source_system" : env.str('IRODS_API_STAGING_SOURCE_SYSTEM',  default=''),  
  "target_system": env.str('IRODS_API_STAGING_TARGET_SYSTEM',  default=''),  
  "target_path_base": env.str('IRODS_API_STAGING_TARGET_PATH_BASE',  default=''),  
  "service": env.str('IRODS_API_STAGING_SERVICE',  default=''),  
  "sslVerification": 'True' == env.bool('IRODS_API_STAGING_SSL_VERIFICATION',  default=None),  
  "encryption_service": env.str('IRODS_API_ENCRYPTION_SERVICE', default=''),
#  "zones": json.loads (env.str('IRODS_API_STAGING_ZONES', default='')),
## workaround while we investigate why the template is not working for this key.
  "zones":  {},
}

