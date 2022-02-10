import irods.exception
from irods.session import iRODSSession
from irods.access import iRODSAccess
from irods.exception import (CAT_INVALID_USER)
import hashlib
from . import group
from . import utils
import logging

logger = logging.getLogger(__name__)

def create_project(session, zone, project_name):
    """Create a project on the DDI. This includes creating the necessary directories, groups, and setting the rights

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    proj_hash = utils.hash( project_name) 
    coll_user = "/%s/user/%s" % (zone, proj_hash)
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    coll_public = "/%s/public/%s" % (zone, proj_hash)

    session.collections.create(coll_user)
    session.collections.get(coll_user).metadata.add('ShortProject', project_name)

    session.collections.create(coll_project)
    session.collections.get(coll_project).metadata.add('ShortProject', project_name)

    session.collections.create(coll_public)
    session.collections.get(coll_public).metadata.add('ShortProject', project_name)

    acl_project = iRODSAccess('inherit', coll_project)
    acl_public = iRODSAccess('inherit', coll_public)
    session.permissions.set(acl_project)
    session.permissions.set(acl_public)

    acl_project_rodsadmin = iRODSAccess('own', coll_project, "rodsadmin")
    session.permissions.set(acl_project_rodsadmin)

    acl_public_rodsadmin = iRODSAccess('own', coll_public, "rodsadmin")
    session.permissions.set(acl_public_rodsadmin)

    group.create_project_group(session, project_name)
    group.set_project_group_rights(session, zone, project_name)
    group.create_project_admin_group(session, project_name)
    group.set_project_group_adm_rights(session, zone, project_name)

def remove_project(session, zone, project_name):
    """Delete a project on the DDI. This includes deleting the necessary directories, groups, and revoking the rights

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    proj_hash = "proj" + hashlib.md5(project_name.encode()).hexdigest()
    coll_user = "/%s/user/%s" % (zone, proj_hash)
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    session.collections.remove(coll_user, recurse=True, force=True)
    session.collections.remove(coll_project, recurse=True, force=True)
    project_group = session.user_groups.get(project_name)
    project_admin_group = session.user_groups.get(project_name+"_mgr")
    project_group.remove()
    project_admin_group.remove()

def create_new_user_directories(session, zone, project_name, user, federated_zones):
    """Create the necessary directories for a new user on the DDI. This includes setting the rights for the newly created directories

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    proj_hash = utils.hash( project_name) 
    coll_user = "/%s/user/%s/%s" % (zone, proj_hash, user)
    session.collections.create(coll_user)
    acl_inherit = iRODSAccess('inherit', coll_user)
    session.permissions.set(acl_inherit)
    acl_user = iRODSAccess("own", coll_user, user, zone)
    session.permissions.set(acl_user)
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        acl_user_fed = iRODSAccess("own", coll_user, user, fed_zone)
        try:
            session.permissions.set(acl_user_fed)
        except irods.exception.iRODSException as e:
            logger.error("Error giving access to user directories for federated user {0}: {1}".format(username, e))


def remove_user_directories(session, zone, project_name, user):
    """Remove the necessary directories for a user on the DDI. This includes revoking the rights for his/her user directories

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    proj_hash = utils.hash( project_name) 
    coll_user = "/%s/user/%s/%s" % (zone, proj_hash, user)
    session.collections.remove(coll_user, recurse=True, force=True)

def update_new_admin_user_directories(session, zone, project_name, user, federated_zones):
    """Create the necessary directories for a new admin user on the DDI. This includes setting the rights for the newly created directories

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    proj_hash = utils.hash( project_name) 
    coll_user = "/%s/user/%s/%s" % (zone, proj_hash, user)
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    acl_user = iRODSAccess("write", coll_user, user, zone)
    acl_project = iRODSAccess("write", coll_project, user, zone)
    session.permissions.set(acl_user)
    session.permissions.set(acl_project)
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        acl_user = iRODSAccess("write", coll_user, user, fed_zone)

        try:
          session.permissions.set(acl_user)
        except irods.exception.iRODSException as e:
          logger.error("Error giving admin access to user directories for federated user {0}: {1}".format(username, e))

        acl_project = iRODSAccess("write", coll_project, user, fed_zone)
        try:
            session.permissions.set(acl_project)
        except irods.exception.iRODSException as e:
            logger.error("Error giving admin access to user directories for federated user {0}: {1}".format(username, e))

def create_new_admin_user_directories(session, zone, project_name, user, federated_zones):
    """Create the necessary directories for a new admin user on the DDI. This includes setting the rights for the newly created directories

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    proj_hash = utils.hash( project_name) 
    coll_user = "/%s/user/%s/%s" % (zone, proj_hash, user)
    session.collections.create(coll_user)
    acl_user = iRODSAccess("write", coll_user, user, zone)
    session.permissions.set(acl_user)
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        acl_user = iRODSAccess("write", coll_user, user, fed_zone)
        try:
            session.permissions.set(acl_user)
        except irods.exception.iRODSException as e:
            logger.error("Error giving admin access to user directories for federated user {0}: {1}".format(username, e))

def freeze_dataset(session, zone, project_name, dataset, user):
    """Freeze a dataset in the public directory. This can be only done by a project admin user i.e a member of the project admin group

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.

    dataset: str
        The name of the dataset to be frozen

    user: str
        The user that wants to freeze the dataset
    """
    admin_group = session.user_groups.get(project_name+"_mgr")
    members = admin_group.members
    proj_hash = utils.hash( project_name) 
    for a_user in members:
        if a_user.name == user:
            coll_dataset = "/%s/public/%s/%s" % (zone, proj_hash, dataset)
            acl_dataset_admin = iRODSAccess("null", coll_dataset, admin_group, zone)
            acl_dataset = iRODSAccess("null", coll_dataset, project_name, zone)
            session.permissions.set(acl_dataset_admin)
            session.permissions.set(acl_dataset)

        else:
            print("Operation is only supported for project admins")
