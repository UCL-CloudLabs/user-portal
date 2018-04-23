"""Miscelanneous methods for working with Azure."""

from functools import wraps
import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient

from .host_status import HostStatus
from .names import group_name, vm_name
from .secrets import Secrets


logger = logging.getLogger("cloudlabs.azure")


def log(action_name):
    """Logs the start and end of a method, referencing the given action name."""
    def wrap(f):
        @wraps(f)
        def helper(self, host):
            logger.debug(
                "Asking Azure to %s host %s", action_name, host.id
            )
            f(self, host)
            logger.debug(
                "Azure completed request to %s host %s",
                action_name, host.id
            )
        return helper
    return wrap


class AzureTools(object):
    """A class offering common functionality for Azure VMs.

    Note that all the methods for managing VMs in this class block until the
    requested action completes. More specifically, the Azure API calls (start,
    stop etc) return immediately, and we then have to execute the returned
    instruction and wait for it to complete.

    Also see: https://github.com/Azure-Samples/virtual-machines-python-manage
    """

    def __init__(self):
        self.refresh()

    @log("start")
    def start_VM(self, host):
        """Start an Azure VM."""
        action = self.cmc.virtual_machines.start(group_name(host), vm_name(host))
        action.wait()

    @log("restart")
    def restart_VM(self, host):
        """Restart an already running Azure VM.."""
        action = self.cmc.virtual_machines.restart(group_name(host), vm_name(host))
        action.wait()

    @log("stop")
    def stop_VM(self, host):
        """Deallocate an Azure VM."""
        # Stop the VM: the call to deallocate returns immediately, and then we
        # have to execute the returned instruction and wait for it to complete.
        # Note that we need to call deallocate and not power_off, since the
        # latter only stops the machine but continues charging for it.
        action = self.cmc.virtual_machines.deallocate(group_name(host), vm_name(host))
        action.wait()

    @log("delete the resource group of")
    def delete_VM(self, host):
        """Delete an Azure VM and all associated resources."""
        action = self.rmc.resource_groups.delete(group_name(host))
        action.wait()

    def refresh(self):
        """Set up or refresh the authentication info and management clients."""
        logger.info("Refreshing Azure credentials")
        self.credentials, self.subscription_id = self._get_credentials()
        self.cmc = ComputeManagementClient(self.credentials, self.subscription_id)
        self.rmc = ResourceManagementClient(self.credentials, self.subscription_id)

    def get_status(self, host):
        """Return the status of a host deployed on Azure."""
        # Getting the status is not obvious at first glance. This has some info:
        # https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/virtualmachines-state
        # TODO Consider making this static or having a static version
        try:
            group = group_name(host)
            vm = vm_name(host)
            # The InstanceViewStatus object returned has a code attribute and a
            # slightly more human-readable display_status. The code seems to follow
            # a particular structure, so it's probably best to work with that.
            statuses = [
                status.code
                for status
                in self.cmc.virtual_machines.instance_view(group, vm).statuses
            ]
        except Exception as e:
            return HostStatus.unknown
        prov_state = _get_provisioning_state_azure(statuses)
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
                if power_state == "deallocated":
                    return HostStatus.stopped
                elif power_state == "starting":
                    return HostStatus.starting
                elif power_state == "running":
                    return HostStatus.running
                elif (power_state == "deallocating" or power_state == "stopping"
                      or power_state == "stopped"):
                    # "stopped" still incurs charging; "deallocated" means truly off
                    return HostStatus.stopping
            return HostStatus.error  # uknown status, return error

    def _get_credentials(self):
        """Get the necessary credentials for creating the management clients."""
        subscription_id = Secrets.TF_VAR_azure_subscription_id
        credentials = ServicePrincipalCredentials(
            client_id=Secrets.TF_VAR_azure_client_id,
            secret=Secrets.TF_VAR_azure_client_secret,
            tenant=Secrets.TF_VAR_azure_tenant_id
        )
        return credentials, subscription_id


def _remove_prefix(string, prefix):
    # inspired from
    # https://stackoverflow.com/questions/16891340/remove-a-prefix-from-a-string
    # but maybe we don't need it
    return string[len(prefix):] if string.startswith(prefix) else string


def _get_provisioning_state_azure(statuses):
    for status in statuses:
        if status.startswith("ProvisioningState/"):
            return _remove_prefix(status, "ProvisioningState/")
    assert False  # should never happen
    return None
