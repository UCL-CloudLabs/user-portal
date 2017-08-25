
import os

from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app

from . import create_celery
from ..app import create_app
from ..deployer.deployer import Deployer
from ..host_status import HostStatus
from ..models import Host


celery = create_celery(
    create_app(
        os.getenv('APP_SETTINGS', 'cloudlabs.config.Config')))


@celery.task(name='cloudlabs.deploy')
def deploy(host_id):
    try:
        host = Host.query.get(host_id)
        if host is None:
            # Host was deleted already
            return
        deployer = Deployer(current_app.root_path)
        deployer.deploy(host)
    except SoftTimeLimitExceeded:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nTime limit exceeded - deployment terminated!\n')
