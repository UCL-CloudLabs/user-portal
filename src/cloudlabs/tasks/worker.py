
import traceback

from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app

from . import create_celery
from ..app import create_app
from ..deployer.deployer import Deployer
from ..host_status import HostStatus
from ..models import Host
from ..secrets import apply_secrets


apply_secrets()
celery = create_celery(create_app())


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
    except Exception as e:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nUnexpected error!\n' + traceback.format_exc(e))


@celery.task(name='cloudlabs.destroy')
def destroy(host_id):
    try:
        host = Host.query.get(host_id)
        if host is None or host.status is HostStatus.defining:
            # Host was deleted already
            return
        deployer = Deployer(current_app.root_path)
        deployer.destroy_host(host)
    except SoftTimeLimitExceeded:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nTime limit exceeded - destruction failed!\n')
    except Exception as e:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nUnexpected error!\n' + traceback.format_exc(e))
