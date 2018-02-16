import signal
import traceback

from celery.exceptions import SoftTimeLimitExceeded
from flask import current_app

from . import create_celery
from ..app import create_app
from ..azure_tools import AzureTools
from ..deployer.deployer import Deployer
from ..host_status import HostStatus
from ..models import Host
from ..secrets import apply_secrets


apply_secrets()
celery = create_celery(create_app())


def catch_signal(signum, frame):
    # TODO Do we actually need this? The intention was to catch the termination
    # signal from revoke so that the worker process doesn't die. It might be
    # that this is redundant, though.
    # print("Caught signal")   # DEBUG
    raise RuntimeError


@celery.task(name='cloudlabs.deploy')
def deploy(host_id):
    signal.signal(signal.SIGTERM, catch_signal)
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
    except RuntimeError:  # if terminated -- to prevent worker being killed
        pass
    except Exception as e:
        host.update(status=HostStatus.error,
                    deploy_log=host.deploy_log +
                    '\n\nUnexpected error!\n' + traceback.format_exc(e))


@celery.task(name='cloudlabs.destroy')
def destroy(host_id, hard):
    # print("Destroying {} from task {}".format(host_id, deploy.request.id))  # DEBUG
    try:
        host = Host.query.get(host_id)
        if host is None or host.status is HostStatus.defining:
            # Host was deleted already
            return
        deployer = Deployer(current_app.root_path)
        if hard:
            deployer.hard_delete(host)
        else:
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
    finally:
        # Regardless of how the task ends, mark the deployment as finished
        # print("Unsetting task ID")  # DEBUG
        host.update(task=None)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, refresh_status.s(),
                             name='Refresh the DB')


@celery.task(name='cloudlabs.refresh_status')
def refresh_status():
    tools = AzureTools()
    # TODO better to use query.filter(Host.status not in [...])? (if possible)
    for host in Host.query.all():
        # If we believe the host is still being defined/deployed, ignore the
        # live status. This is because, as far as Azure is concerned, the VM
        # may be running or nonexistent, but we don't want to display that to
        # the owner just yet.
        # TODO maybe exclude error state too? (potentially set during deployment)
        if host.status not in [HostStatus.defining, HostStatus.deploying]:
            status = tools.get_status(host)
            host.update(status=status)
