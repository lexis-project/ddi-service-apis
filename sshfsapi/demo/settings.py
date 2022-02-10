#irods configuration
IRODS = {
  'openid_microservice':'https://<broker>',
}

SSHFS= {
       'path': '<sshfs mounted path>',
       "userlen": 10,
       'host': "<host>",
       "group": "sftponly",
       "keydir": '<directory with keys>'
}
