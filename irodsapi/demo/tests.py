from django.test import TestCase
from demo import keycloak_api
from demo import sync
import logging

logger = logging.getLogger(__name__)
# logging.disable(logging.NOTSET)
# logger.setLevel(logging.DEBUG)


class KeycloakTestCase(TestCase):
    def setUp(self):
        logger.info("Setting up")

    def test_list_user_groups(self):
        logger.info("Getting Keycloak groups")
        user_groups = keycloak_api.list_user_groups()
        self.assertTrue(len(user_groups) > 0)
        print(user_groups)

    def test_list_project_groups(self):
        logger.info("Getting Keycloak groups")
        projects = keycloak_api.list_project_groups()
        self.assertTrue(len(projects) > 0)
        print(projects)

    def test_sync_projects(self):
        logger.info("Getting Keycloak groups")
        sync.sync_projects()

    def test_sync_users(self):
        logger.info("Getting iRODS groups")
        sync.sync_users()

    def test_log(self):
        logger.info("Log test info")
        logger.warning("Log test warning")
        logger.error("Log test error")
        logger.debug("Log test debug")