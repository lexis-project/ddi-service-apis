import irods.exception
from irods.session import iRODSSession
from irods.access import iRODSAccess
from irods.exception import (CAT_INVALID_USER, CATALOG_ALREADY_HAS_ITEM_BY_THAT_NAME)
from irods.models import User, UserGroup
from irods.user import iRODSUser, iRODSUserGroup
from . import group
from . import projects
import logging

logger = logging.getLogger(__name__)


def create_user(session, user, user_type, zone, federated_zones, auth_str):
    """Create a user on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be created (no #zone, user at all zones created)

    user_type: str
        type of user created. Usually it's set to rodsuser

    zone: str
        îRODS zone to create the user on

    auth_str: str
        The aua value used for authentication

    federated_zones: list of str
        federated zones where the user exists
    """
    session.users.create(user, user_type, zone, auth_str)
    group.add_newuser_to_lexis_group(session, user)
    home_dir = "/" + zone + "/home/" + user
    acl_rods = iRODSAccess("own", home_dir, 'rodsadmin', zone)
    session.permissions.set(acl_rods, admin=True)
    acl_home = iRODSAccess('inherit', home_dir)
    session.permissions.set(acl_home, admin=True)
    for fed_zone in federated_zones:
        try:
            session.users.create(user, user_type, fed_zone, auth_str)
            username = user + "#" + fed_zone
            group.add_newuser_to_lexis_group(session, username)
            acl_user_fed = iRODSAccess("own", home_dir, user, fed_zone)
            session.permissions.set(acl_user_fed)
        except irods.exception.iRODSException as e:
            logger.error("Error creating federated user {0}: {1}".format(user, e))

def delete_user(session, user, federated_zones):
    """Remove a user on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be deleted (
    """
    user_session = session.users.get(user)
    user_session.remove()
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        fed_user = session.users.get(username)
        fed_user.remove()

def add_user_to_project(session, project_name, user, zone, federated_zones):
    """Add a user to a project on the DDI.

    Parameters
    ----------
    project_name: str
        The name of the project.
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be added to the project (no #zone, user at all zones added)

    zone: str
        local iRODS zone of the user

    federated_zones: list of str
        federated zones where the user exists
    """
    try:
        group.add_user_to_proj_group(session, user, project_name)
    except irods.exception.iRODSException as e:
        logger.error("Error adding user {0} to project {1}: {2}".format(user, project_name, e))
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        try:
            group.add_user_to_proj_group(session, username, project_name)
        except irods.exception.iRODSException as e:
            logger.error("Error adding federated user {0} to project {1}: {2}".format(username, project_name, e))
        projects.create_new_user_directories(session, zone, project_name, user, federated_zones)

def remove_user_from_project(session, project_name, user, zone, federated_zones):
    """Remove a user to a project on the DDI.

    Parameters
    ----------
    project_name: str
        The name of the project.
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be removed

    zone: str
        iRODS zone to create the user on

    federated_zones: list of str
        federated zones where the user exists
    """
    group.remove_user_from_proj_group(session, user, project_name)
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        try:
            group.remove_user_from_proj_group(session, username, project_name)
        except irods.exception.iRODSException as e:
            logger.error("Error removing user {0} from project {1}: {2}".format(username, project_name, e))
    projects.remove_user_directories(session, zone, project_name, user)

def add_admin_user_to_project(session, project_name, user, zone, federated_zones):
    """Add a user as an admin to a project on the DDI.

    Parameters
    ----------
    project_name: str
        The name of the project.
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be added (no #zone, user at all zones added)

    zone: str
        iRODS zone to create the user on

    federated_zones: list of str
        federated zones where the user exists
    """
    try:
        group.add_user_to_proj_admin_group(session, user, project_name)
    except irods.exception.iRODSException as e:
        logger.error("Error adding admin user {0} to project {1}: {2}".format(user, project_name, e))

    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        try:
            group.add_user_to_proj_admin_group(session, username, project_name)
        except irods.exception.iRODSException as e:
            logger.error("Error adding federated admin user {0} to project {1}: {2}".format(username, project_name, e))
    projects.update_new_admin_user_directories(session, zone, project_name, user, federated_zones)

def revoke_admin_status_to_user(session, project_name, user, federated_zones):
    """Revoke user admin status to a project on the DDI.

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    user: str
        Name of the user to be removed from group (no #zone, user at all zones removed)

    project_name: str
        The name of the project.

    federated_zones: list of str
        federated zones where the user exists
    """
    group.remove_user_from_proj_admin_group(session, user, project_name)
    for fed_zone in federated_zones:
        username = user + "#" + fed_zone
        try:
            group.remove_user_from_proj_admin_group(session, username, project_name)
        except irods.exception.iRODSException as e:
            logger.error("Error removing user {0} from project admin group {1}:{2}".format(username, project_name, e))

def list_all_users(session):
    """ List all users in the session iRODS zone

    Parameters
    ----------
    session : iRODS session object
        an object that setup a session with iRODS

    Return
    ------
    dict with key -> username, value -> group membership
    """
    groups = {}
    for group in session.query(UserGroup,User).filter(User.type == 'rodsuser'):
        grp = iRODSUserGroup(session.user_groups, group)
        usr = iRODSUser(session.users, group)

        # Skip grp with same id as user - just iRODS thing
        if grp.id == usr.id:
           continue

        if usr.name in groups:
            groups[usr.name].add(grp.name)
        else:
            groups[usr.name] = {grp.name}
    return groups
