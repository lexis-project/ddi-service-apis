import irods.exception
from irods.session import iRODSSession
from irods.access import iRODSAccess
from irods.exception import (CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME)
from . import utils
import logging

logger = logging.getLogger(__name__)


def create_lexis_group_(session):
    """Create lexis group on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    """
    session.user_groups.create("lexis_group")

def set_lexis_group_rights(session,zone):
    """Set the right of lexis group on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on
    """
    group = "lexis_group"
    coll_user = "/%s/user" % (zone)
    coll_project = "/%s/project" % (zone)
    coll_public = "/%s/public" % (zone)
    acl_user = iRODSAccess("read", coll_user, group, zone)
    acl_project = iRODSAccess("read", coll_project, group, zone)
    acl_public = iRODSAccess("read", coll_public, group, zone)
    session.permissions.set(acl_user)
    session.permissions.set(acl_project)
    session.permissions.set(acl_public)

def add_newuser_to_lexis_group(session, user):
    """Add new user to lexis group.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be added (u#Z when needed)
    """
    group = session.user_groups.get("lexis_group")
    group.addmember(user)

def create_lexis_sup_group(session):
    """Create lexis support on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    """
    session.user_groups.create("lexis_sup")

def add_newuser_to_lexis_sup_group(session, user):
    """Add new user to lexis support.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be added (u#Z when needed)
    """
    group = session.user_groups.get("lexis_sup")
    group.addmember(user)

def set_consent_based_right_to_lexis_sup(session,zone, project_name):
    """Set the right of lexis support for a certain project on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    group = "lexis_sup"
    proj_hash = utils.hash( project_name) 
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    acl_project = iRODSAccess("write", coll_project, group, zone)
    session.permissions.set(acl_project)
    irods_coll_project = session.collections.get(coll_project)
    for col_datasets in irods_coll_project.subcollections:
        for col in col_datasets.subcollections:
            acl_details = iRODSAccess("null", col, group, zone)
            try:
                session.permissions.set(acl_details)
            except irods.exception.iRODSException as e:
                logger.error("Error setting lexis_support ACL on collection {0}".format(col.path))

def revoke_consent_based_right_to_lexis_sup(session,zone, project_name):
    """Revoke the right of lexis support for a certain project on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    group = "lexis_sup"
    proj_hash = utils.hash( project_name) 
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    acl_project = iRODSAccess("null", coll_project, group, zone)
    session.permissions.set(acl_project)

def create_lexis_adm_group(session):
    """Create lexis admin on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    """
    session.user_groups.create("lexis_adm")

def add_newuser_to_lexis_adm_group(session, user):
    """Add new user to lexis admin.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be added (u#Z when needed)
    """
    group = session.user_groups.get("lexis_adm")
    group.addmember(user)

def set_consent_based_right_to_lexis_adm(session,zone, project_name):
    """Set the right of lexis admin for a certain project on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    group = "lexis_adm"
    proj_hash = utils.hash( project_name) 
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    acl_project = iRODSAccess("read", coll_project, group, zone)
    session.permissions.set(acl_project)
    irods_coll_project = session.collections.get(coll_project)
    for col_datasets in irods_coll_project.subcollections:
        col_datasets_name = col_datasets.name
        acl_dataset = iRODSAccess("write", col_datasets_name, group, zone)
        try:
            session.permissions.set(acl_dataset)
        except irods.exception.iRODSException as e:
            logger.error("Error assigning lexis_adm ACL to collection {0}: {1}".format(col_datasets.path, e))
        for col in col_datasets.subcollections:
            acl_details = iRODSAccess("null", col, group, zone)
            try:
                session.permissions.set(acl_details)
            except irods.exception.iRODSException as e:
                logger.error("Error assigning lexis_adm ACL to subcollection {0}: {1}".format(col.path, e))

def revoke_consent_based_right_to_lexis_adm(session,zone, project_name):
    """Revoke the right of lexis admin for a certain project on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    group = "lexis_adm"
    proj_hash = utils.hash( project_name) 
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    acl_project = iRODSAccess("null", coll_project, group, zone)
    session.permissions.set(acl_project)

def create_project_group(session, project_name):
    """Create new project group on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    project_name: str
        The name of the project.
    """
    session.user_groups.create(project_name)

def set_project_group_rights(session, zone, project_name):
    """Set project group rights on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    group = project_name
    proj_hash = utils.hash( project_name) 
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    coll_public = "/%s/public/%s" % (zone, proj_hash)
    acl_project = iRODSAccess("own", coll_project, group, zone)
    acl_public = iRODSAccess("null", coll_public, group, zone)
    session.permissions.set(acl_project)
    session.permissions.set(acl_public)

def add_user_to_proj_group(session, user, project_name):
    """Add new user to a certain project.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be added (u#Z when needed)

    project_name: str
        The name of the project.
    """
    group = session.user_groups.get(project_name)
    group.addmember(user)

def remove_user_from_proj_group(session, user, project_name):
    """Remove a user from a certain project.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user tobe added

    project_name: str
        The name of the project.
    """
    group = session.user_groups.get(project_name)
    group.removemember(user)

def create_project_admin_group(session, project_name):
    """Create new project admin group on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    project_name: str
        The name of the project.
    """
    session.user_groups.create(project_name+"_mgr")

def set_project_group_adm_rights(session, zone, project_name):
    """Set project group admin rights on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    zone: str
        îRODS zone to create the user on

    project_name: str
        The name of the project.
    """
    group = project_name+"_mgr"
    proj_hash = utils.hash( project_name) 
    coll_project = "/%s/project/%s" % (zone, proj_hash)
    coll_public = "/%s/public/%s" % (zone, proj_hash)
    acl_project = iRODSAccess("own", coll_project, group, zone)
    acl_public = iRODSAccess("write", coll_public, group, zone)
    session.permissions.set(acl_project)
    session.permissions.set(acl_public)
    irods_coll_project = session.collections.get(coll_project)
    irods_coll_project_public = session.collections.get(coll_public)
    for col_datasets in irods_coll_project.subcollections:
        col_datasets_name = col_datasets.name
        acl_dataset = iRODSAccess("own", col_datasets_name, group, zone)
        try:
            session.permissions.set(acl_dataset)
        except irods.exception.iRODSException as e:
            logger.error("Error setting project group admin to collection {0}: {1}".format(col_datasets.path, e))

        for col in col_datasets.subcollections:
            acl_details = iRODSAccess("own", col, group, zone)
            try:
                session.permissions.set(acl_details)
            except irods.exception.iRODSException as e:
                logger.error("Error setting project group admin to subcollection {0}: {1}".format(col.path, e))

    for col_datasets in irods_coll_project_public.subcollections:
        col_datasets_name = col_datasets.name
        acl_dataset = iRODSAccess("null", col_datasets_name, group, zone)
        try:
            session.permissions.set(acl_dataset)
        except irods.exception.iRODSException as e:
            logger.error("Error setting project group admin to public collection {0}: {1}".format(col_datasets.path, e))

        for col in col_datasets.subcollections:
            acl_details = iRODSAccess("null", col, group, zone)
            try:
                session.permissions.set(acl_details)
            except irods.exception.iRODSException as e:
                logger.error(
                    "Error setting project group admin to public subcollection {0}: {1}".format(col_datasets.path, e))


def add_user_to_proj_admin_group(session, user, project_name):
    """Add new user to a certain project admin group.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user tobe added

    project_name: str
        The name of the project.
    """
    group = session.user_groups.get(project_name+"_mgr")
    try:
      group.addmember(user)
    except CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME:
      logger.error("User "+user+" already belongs to "+project_name+"_mgr, skipping")

def remove_user_from_proj_admin_group(session, user, project_name):
    """Remove a user from a certain project's admin group.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user tobe added

    project_name: str
        The name of the project.
    """
    group = session.user_groups.get(project_name+"_mgr")
    group.removemember(user)

def check_user_project_membership(session, user, project_name):
    """Check if a user belongs to a project.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user tobe added

    project_name: str
        The name of the project.
    """
    project_group = session.user_groups.get(project_name)
    members = project_group.members
    for a_user in members:
        if a_user.name == user:
            return True
    return False

def check_adm_user_project_membership(session, user, project_name):
    """Check if a user is an admin to project.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user tobe added

    project_name: str
        The name of the project.
    """
    project_adm_group = session.user_groups.get(project_name+"_mgr")
    members = project_adm_group.members
    for a_user in members:
        if a_user.name == user:
            return True
    return False
    
def remove_user_from_lexis_sup_group(session, user):
    """Remove a user from lexis support project.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be removed
    """
    group = session.user_groups.get("lexis_sup")
    group.removemember(user)
    
def remove_user_from_lexis_adm_group(session, user):
    """Remove a user from lexis admin project.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be removed
    """
    group = session.user_groups.get("lexis_adm")
    group.removemember(user)

