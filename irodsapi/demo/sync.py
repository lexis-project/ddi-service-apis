from demo import keycloak_api
import irods.session
import logging
from irodsApisForWp8 import projects, user
import demo.settings
from irods.exception import iRODSExceptionMeta, iRODSException

logger = logging.getLogger(__name__)

# Groups to ignore when checking membership in irods
GROUPS_IGNORE = ["lexis_group","lexis_sup","public","lexis_adm","rodsadmin"]

# Usernames to ignore
USERS_IGNORE = ["rods"]

def get_irods_session():
    """
    Provides iRODS session from credentials in settings - the iRODS user has to be of type 'rodsadmin'
    :return: iRODSSession
    """
    return irods.session.iRODSSession(
        host=demo.settings.IRODS['host'], port=1247,
        zone=demo.settings.IRODS['zone'], user=demo.settings.IRODS['user'], password=demo.settings.IRODS['pwd'])

def list_projects_irods(session):
    """
    Lists all projects in iRODS by readin ShortProject meta in /zone/project/* collections
    :param session: iRODSSession
    :return: List of project shortnames
    """
    projects_list = []
    prj_root = session.collections.get('/{0}/project'.format(demo.settings.IRODS['zone']))
    for projects in prj_root.subcollections:
        projects_list.append({'hash': projects.name, 'shortname': projects.metadata.get_one('ShortProject').value})

    return projects_list


def sync_projects():
    """
    Sync projects from Keycloak to iRODS.
    """
    logger.info("Syncing projects")
    keycloak_projects = keycloak_api.list_project_groups()
    logger.info("Got {0} projects from Keycloak".format(len(keycloak_projects)))

    irods_projects = list_projects_irods(get_irods_session())
    logger.info("Got {0} projects from iRODS ".format(len(irods_projects)))

    # Get project name sets
    keycloak_set = set([x['prj'] for x in keycloak_projects])
    irods_set = set([x['shortname'] for x in irods_projects])

    # Get their difference
    projects_create = keycloak_set - irods_set

    # Create new projects if diff is not empty
    if projects_create:
        logger.info("Found {0} new projects".format(len(projects_create)))
        session = get_irods_session()
        zone = demo.settings.IRODS['zone']
        for project in projects_create:
            logger.info("Creating project {0}".format(project))
            # Call WP8 API create project
            try:
                projects.create_project(session, zone, project)
            except iRODSException as e:
                logger.error("iRODS error when creating project {0}: {1}".format(project, e))
    else:
        logger.info("No new project found in Keycloak.")

    # Check for orphan projects in iRODS
    projects_orphan = irods_set - keycloak_set
    if projects_orphan:
        logger.info("Found {0} orphan projects in iRODS".format(len(projects_orphan)))
        for project_orphan in projects_orphan:
            logger.info(project_orphan)

def map_keycloak_groups_to_irods(groups):
    """
     :param groups - list of dicts with id, name and path of the group in Keycloak
     :return: list with corresponding irods groups mapped

     This code expects that attributes in Keycloak groups are stored in following format:

      'attributes': {'DAT_WRITE': ['{"ORG_UUID":"<UUID>","PRJ":"project_shortname","PRJ_UUID":"<UUID>>"}']}

     Where the key is always a name of the group in KC and its value is a list with single item which is a dict with the
     contents shown above.
     """

    # These groups are mapped to basic group in iRODS i.e. without _mgr
    BASIC_GROUPS = {'DAT_LIST', 'DAT_WRITE', 'DAT_READ'}

    # These groups are mapped to mgr_ groups in iRODS
    MGR_GROUPS = BASIC_GROUPS | {'DAT_PUBLISH'}

    # Create a dictionary where key -> project shortname and value -> KC groups without UUID
    project_shortname_map = {}
    for group in groups:
        if group['name'].startswith('DAT_'):
            # Get project shortname from group attributes in Keycloak
            # Take first item from the attributes dict
            group_details = keycloak_api.get_group_attributes(keycloak_api.get_keycloak_admin(), group['id']).popitem()
            grp_name = group_details[0]
            project_shortname = group_details[1]['PRJ']

            # Add the project shortname to dict which contains sets of all groups in Keycloak for that particular prj
            if project_shortname in project_shortname_map:
                project_shortname_map[project_shortname].add(grp_name)
            else:
                project_shortname_map[project_shortname] = {grp_name}

    # Map the groups
    mapped_irods_groups = []
    for project_shortname, keycloak_groups in project_shortname_map.items():

        # Check if keycloak_groups have all groups required to have the basic group assignment
        # i.e. difference of the sets is empty
        if not BASIC_GROUPS - keycloak_groups:
            mapped_irods_groups.append(project_shortname)

        # Check if keycloak_groups have all groups required to have the mgr group assignment
        # i.e. difference of the sets is empty
        if not MGR_GROUPS - keycloak_groups:
            mapped_irods_groups.append("{0}_mgr".format(project_shortname))

    return mapped_irods_groups

def sync_users():
    """
    Sync users from Keycloak to iRODS and assign them to proper projects according to groups in Keycloak
    """
    logger.info("Syncing users")
    keycloak_users = keycloak_api.list_user_groups()
    logger.info("Got {0} users from Keycloak".format(len(keycloak_users)))

    irods_users = user.list_all_users(get_irods_session())
    logger.info("Got {0} users from iRODS".format(len(irods_users)))

    kc_user_set = set([ u for u in keycloak_users])
    irods_user_set = set([ u for u in irods_users])

    # Get difference between Keycloak and iRODS users - the result is set of users missing in irods
    users_create = kc_user_set - irods_user_set

    # Map Keycloak groups to iRODS groups
    keycloak_users_mapped = {}
    for kc_user, kc_user_meta in keycloak_users.items():
        logger.info("Mapping user {0}".format(kc_user))
        keycloak_users_mapped[kc_user] = map_keycloak_groups_to_irods(kc_user_meta['groups'])


    # Create users which are not in iRODS yet
    session = get_irods_session()
    for user_name in users_create:
        # User has no DAT_ groups is Keycloak, skip
        #if not keycloak_users_mapped[user_name]:
        #    continue

        # Skip ignored usernames
        if user_name in USERS_IGNORE:
            logging.info("Skipping user {0} ({1})".format(user_name, keycloak_users[user_name]['id']))
            continue

        logger.info("Creating user {0} ({1})".format(user_name, keycloak_users[user_name]['id']))
        try:
            user.create_user(session, user_name, 'rodsuser', demo.settings.IRODS['zone'], demo.settings.IRODS['federated'], keycloak_users[user_name]['id'])
        except iRODSException as e:
            logger.error("iRODS error when creating user {0}: {1}".format(user_name, e))

    # Get new users from irods
    irods_users = user.list_all_users(get_irods_session())
    logger.info("Got {0} users from iRODS after creation".format(len(irods_users)))

    # Handle only users which are also in Keycloak / do not handle orphan users in iRODS
    irods_user_set = set([u for u in irods_users]).intersection(kc_user_set)

    # Update user groups for existing users in iRODS
    #for kc_user, kc_user_groups in keycloak_users_mapped.items():
    for irods_user in irods_user_set:
        # Add user to iRODS groups where is not assigned
        # The resulting set is sorted such that XXX_mgr group always comes AFTER the non mgr group XXX
        groups_to_add = list(set(keycloak_users_mapped[irods_user]) - irods_users[irods_user])
        groups_to_add.sort()
        for group_to_add in groups_to_add:
            try:
                logger.info("Adding user {0} to group {1}".format(irods_user, group_to_add))
                if group_to_add.endswith('_mgr'):
                     # Adding as admin
                     # Trim _mgr from group name - user.add_admin_user_to_project expects only project ShortName
                     user.add_admin_user_to_project(session, group_to_add.rstrip('_mgr'), irods_user, demo.settings.IRODS['zone'],
                                          demo.settings.IRODS['federated'])
                else:
                    # Adding as regular user
                    user.add_user_to_project(session, group_to_add, irods_user, demo.settings.IRODS['zone'],
                                          demo.settings.IRODS['federated'])
            except iRODSException as e:
                logger.error("iRODS error when adding user {0} to group {1}: {2}".format(irods_user, group_to_add, e))

        # Remove user from groups which are not in Keycloak
        # The resulting set is sorted in reverse such that XXX_mgr group always comes BEFORE the non mgr group XXX
        groups_to_remove = list(irods_users[irods_user] - set(keycloak_users_mapped[irods_user]))
        groups_to_remove.sort(reverse=True)
        for group_to_remove in groups_to_remove:
            # Skip default iRODS groups
            if group_to_remove in GROUPS_IGNORE:
                continue

            logger.info("Removing user {0} from group {1}".format(irods_user, group_to_remove))
            try:
                if group_to_remove.endswith('_mgr'):
                    # Trim _mgr from group name - user.revoke_admin_status_to_user expects only project ShortName
                    user.revoke_admin_status_to_user(session, group_to_remove.rstrip('_mgr'), irods_user, demo.settings.IRODS['federated'])
                else:
                    user.remove_user_from_project(session, group_to_remove, irods_user, demo.settings.IRODS['zone'], demo.settings.IRODS['federated'])
            except iRODSException as e:
                logger.error("iRODS error when removing user {0} from group {1}: {2}".format(irods_user, group_to_remove, e))
