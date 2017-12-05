from enum import Enum

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient

from . import names
from .secrets import Secrets


class HostStatus(Enum):
    """Possible statuses for CloudLabs hosts."""

    defining = 'Defining'    # Not yet started to deploy
    deploying = 'Deploying'  # Deployment in progress
    starting = 'Starting'    # Machine is spinning up; service not live
    running = 'Running'      # Web app is running
    stopped = 'Stopped'      # Machine deployed but not turned on
    stopping = 'Stopping'    # Machine is being stopped
    destroying = 'Destroying'
    error = 'Failed to deploy'


def get_status_azure(host):
    """Return the status of a host deployed on Azure."""
    # Getting the status is not obvious at first glance. This has some info:
    # https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/virtualmachines-state
    # TODO Avoid creating this every time (eg by passing cmc as an argument)
    credentials, subscription_id = get_credentials()
    cmc = ComputeManagementClient(credentials, subscription_id)
    try:
        group_name = names.group_name(host)
        vm_name = names.vm_name(host)
        print(group_name, vm_name)
        # The InstanceViewStatus object returned has a code attribute and a
        # slightly more human-readable display_status. The code seems to follow
        # a particular structure, so it's probably best to work with that.
        statuses = [
            status.code
            for status
            in cmc.virtual_machines.instance_view(group_name, vm_name).statuses
        ]
        print(statuses)
    except Exception as e:
        return HostStatus.error
    prov_state = get_provisioning_state_azure(statuses)
    if prov_state == "deleting":
        return HostStatus.destroying
    else:
        for status in statuses:
            # Look for the (one?) status which holds the PowerState. This would
            # be nicer if we could guarantee that there are always exactly two
            # statuses (provisioning and power), but I'm not sure whether that
            # is true.
            if not status.startswith("PowerState"):
                continue
            power_state = _remove_prefix(status, "PowerState/")
            if power_state == "deallocated" or power_state == "stopped":
                return HostStatus.stopped
            elif power_state == "starting":
                return HostStatus.starting
            elif power_state == "running":
                return HostStatus.running
            elif power_state == "deallocating" or power_state == "stopping":
                return HostStatus.stopping
        return HostStatus.error  # uknown status, return error


def get_credentials():
    """Get the necessary credentials for creating the ComputeManagementClient.

    Also see: https://github.com/Azure-Samples/virtual-machines-python-manage
    """
    # TODO are secrets better accessible in a different way?
    # subscription_id = os.environ['TF_VAR_azure_subscription_id']
    # credentials = ServicePrincipalCredentials(
    #     client_id=os.environ['TF_VAR_azure_client_id'],
    #     secret=os.environ['TF_var_azure_client_secret'],
    #     tenant=os.environ['TF_var_azure_tenant_id']
    # )
    subscription_id = Secrets.TF_VAR_azure_subscription_id
    credentials = ServicePrincipalCredentials(
        client_id=Secrets.TF_VAR_azure_client_id,
        secret=Secrets.TF_VAR_azure_client_secret,
        tenant=Secrets.TF_VAR_azure_tenant_id
    )
    return credentials, subscription_id


def get_provisioning_state_azure(statuses):
    for status in statuses:
        if status.startswith("ProvisioningState/"):
            return _remove_prefix(status, "ProvisioningState/")
    assert False  # should never happen
    return None


def _remove_prefix(string, prefix):
    # inspired from
    # https://stackoverflow.com/questions/16891340/remove-a-prefix-from-a-string
    # but maybe we don't need it
    return string[len(prefix):] if string.startswith(prefix) else string
