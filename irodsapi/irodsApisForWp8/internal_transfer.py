from irods.session import iRODSSession
from irods.access import iRODSAccess
import irods.exception as iRODSExceptions
import time
import os
import humanize
import tempfile
import json
import yaml
import hashlib
from . import utils

metadataSingleValue=  ['identifier', 'title', 'publicationYear', 'resourceType', 'resourceTypeGeneral', 'CustomMetadata' ]
metadataMultiValue= ['creator', 'publisher', 'owner', 'contributor', 'relatedIdentifier',
              'rights', 'rightsURI', 'rightsIdentifier', 'CustomMetadataSchema', 'AlternateIdentifier' ]
#Each alternate identifier  has a sub-property AlternateIdentifierType, concatenate using json.encode
#'CustomMetadata', ''CustomMetadataSchema' are special because they need to be json-stringified.
metadataEUDAT=['EUDAT/FIO', 'EUDAT/FIXED_CONTENT', 'EUDAT/PARENT', 'EUDAT/ROR', 'PID', 'EUDAT/REPLICA']

def datasetMeta(metadata):
    d = dict()
    for x in metadataSingleValue:
        try:
           d[x]=metadata.get_one(x).value
           if x == 'CustomMetadata' :
              d[x]=json.loads(d[x])
        except:
           pass
#           print('Irods metadata for ' + x + ' does not conform to standard, ignoring')
    for x in metadataMultiValue:
           d[x]=[]
           if  x == 'CustomMetadataSchema' or x == 'AlternateIdentifier':
               for y in metadata.get_all(x):
                    #pdb.set_trace()
                    d[x].append (json.loads(y.value))
           else:
               for y in metadata.get_all(x):
                  d[x].append (y.value)
    return d

def create_metadata_file(session, public_collection):
    try:
        public_coll = session.collections.get(public_collection)
    except iRODSExceptions.CollectionDoesNotExist:
        raise NotADirectoryError

    meta = public_coll.metadata
    metadata_raw = datasetMeta(meta)
    metadata_dic = {}
    metadata_dic['meta'] = metadata_raw
    print(metadata_dic)
    print(type(metadata_dic))
    metadata_file = public_collection + "/.metadata"
    print(str(metadata_dic))
    obj = session.data_objects.create(metadata_file)
    temp_name = public_coll.name + '.yml'
    with open(temp_name, 'w') as f_in:
        chunk_size = 2 * 1024 * 1024
        yaml.dump(metadata_dic, f_in, default_flow_style=False)
    f_in.close()
    with obj.open('r+') as f_out: 
         with open(temp_name, 'rb') as f_in:
              while True:
                 chunk = f_in.read(chunk_size)
                 if len(chunk) <= 0:
                    break
                 f_out.write(chunk)
    os.remove(temp_name)
    
def move_dataset_to_public(session, zone, project_name, user, dataset_name):
    """Move dataset from project to public. This can be only done by a project admin user i.e a member of the project admin group

        Parameters
        ----------
        session : iRODS session object
            an object that setup a session with iRODS

        zone: str
            îRODS zone where the data is

        project_name: str
            The name of the project.

        user: str
            The user that wants to freeze the dataset

        dataset_name: str
            The name of the dataset to be moved
    """
    proj_hash = utils.hash( project_name) 
    coll_dataset = "/%s/project/%s/%s" % (zone, proj_hash, dataset_name)
    coll_public_dataset = "/%s/public/%s" % (zone, proj_hash)
    coll = session.collections.get(coll_dataset)
    admin_group = session.user_groups.get("adm_" + project_name)
    members = admin_group.members
    status = False
    rights = coll.metadata.get_all('rightsURI')
    if len(rights) != 0:
        for a_user in members:
            if a_user.name == user:
                session.collections.move(coll_dataset, coll_public_dataset)
                status = True
        if not status:
            print("Operation is only supported for project admins")
    else:
        print("Rights metadata are not added. Please add the required metadata and try again")
    create_metadata_file(session, coll_public_dataset)

def move_dataset_to_project(session, project_name, zone, user, dataset_name, dataset_abs_path):
    """Move dataset from user to project.

        Parameters
        ----------
        session : iRODS session object
            an object that setup a session with iRODS

        zone: str
            îRODS zone where the data is

        project_name: str
            The name of the project.

        user: str
            The user that wants to freeze the dataset

        dataset_name: str
            The name of the dataset to be moved

        dataset_abs_path: str
            The name of the dataset to be moved
    """
    proj_hash = utils.hash( project_name) 
    coll_dataset = "/%s/user/%s/%s" % (zone, proj_hash, user, dataset_abs_path)
    coll_project_dataset = "/%s/project/%s/%s" % (zone, proj_hash, dataset_name)
    session.collections.move(coll_dataset, coll_project_dataset)
    
def share_dataset_between_projects(session, zone, project_name_source, project_name_dest, user, dataset_name):
    """Move dataset from project to another project. This can be only done by a project admin user i.e a member of the project admin group

            Parameters
            ----------
            session : iRODS session object
                an object that setup a session with iRODS

            zone: str
                îRODS zone where the data is

            project_name_source: str
                The name of the project.

            project_name_dest: str
                The destination to copy to.

            user: str
                The user that wants to move the dataset

            dataset_name: str
                The name of the dataset to be moved
        """
    proj_hash_src = utils.hash( project_name_source) 
    proj_hash_dst = utils.hash( project_name_dest) 
    coll_dataset_source = "/%s/project/%s/%s" % (zone, proj_hash_src, dataset_name)
    coll_dataset_destination = "/%s/project/%s" % (zone, proj_hash_dst)
    admin_group = session.user_groups.get("adm_" + project_name_source)
    members = admin_group.members
    status = False
    for a_user in members:
        if a_user.name == user:
            session.collections.move(coll_dataset_source, coll_dataset_destination)
            status = True
    if not status:
        print("Operation is only supported for project admins")
        
