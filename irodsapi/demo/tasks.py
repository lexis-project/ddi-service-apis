import logging
from moz_test.celery import app
from demo import sync

logger = logging.getLogger(__name__)

@app.task(bind=True)
def sync_irods(self):
    logger.info("Syncing iRODS projects now")
    sync.sync_projects()
    logger.info("Syncing iRODS users now")
    sync.sync_users()
