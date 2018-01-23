
import traceback

from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app

from . import create_celery
from ..app import create_app
from ..deployer.deployer import Deployer
from ..host_status import HostStatus, get_status_azure
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
        deployer.destroy(host)
    except SoftTimeLimitExceeded:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nTime limit exceeded - destruction failed!\n')
    except Exception as e:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nUnexpected error!\n' + traceback.format_exc(e))


@celery.task(name='cloudlabs.stop')
def stop(host_id):
    """Stop the host with the specified ID."""
    try:
        host = Host.query.get(host_id)
        if host is None:
            return
        deployer = Deployer(current_app.root_path)
        deployer.stop(host)
    # Note that this doesn't set an error status in the the database!
    except SoftTimeLimitExceeded:
        host.update(deploy_log=host.deploy_log +
                    '\n\nTime limit exceeded - stopping failed!\n')
    except Exception as e:
        host.update(deploy_log=host.deploy_log +
                    '\n\nUnexpected error when stopping!\n' +
                    traceback.format_exc(e))


@celery.task(name='cloudlabs.restart')
def restart(host_id):
    """Restart the host with the specified ID."""
    try:
        host = Host.query.get(host_id)
        if host is None:
            return
        deployer = Deployer(current_app.root_path)
        deployer.restart(host)
    # Note that this doesn't set an error status in the the database!
    except SoftTimeLimitExceeded:
        host.update(deploy_log=host.deploy_log +
                    '\n\nTime limit exceeded - restarting failed!\n')
    except Exception as e:
        host.update(deploy_log=host.deploy_log +
                    '\n\nUnexpected error when restarting!\n' +
                    traceback.format_exc(e))


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, refresh_status.s(),
                             name='Refresh the DB')


@celery.task(name='cloudlabs.refresh_status')
def refresh_status():
    for host in Host.query.all():
        status = get_status_azure(host)
        host.update(status=status)
