"""Miscelanneous methods for working with Azure."""

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient

from .names import group_name, vm_name
from .secrets import Secrets


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

    def start_VM(self, host):
        """Start an Azure VM."""
        action = self.cmc.virtual_machines.start(group_name(host), vm_name(host))
        action.wait()

    def restart_VM(self, host):
        """Restart an already running Azure VM.."""
        action = self.cmc.virtual_machines.restart(group_name(host), vm_name(host))
        action.wait()

    def stop_VM(self, host):
        """Deallocate an Azure VM."""
        # Stop the VM: the call to deallocate returns immediately, and then we
        # have to execute the returned instruction and wait for it to complete.
        # Note that we need to call deallocate and not power_off, since the
        # latter only stops the machine but continues charging for it.
        action = self.cmc.virtual_machines.deallocate(group_name(host), vm_name(host))
        action.wait()

    def delete_VM(self, host):
        """Delete an Azure VM and all associated resources."""
        action = self.rmc.resource_groups.delete(group_name(host))
        action.wait()

    def refresh(self):
        """Set up or refresh the authentication info and management clients."""
        self.credentials, self.subscription_id = self._get_credentials()
        self.cmc = ComputeManagementClient(self.credentials, self.subscription_id)
        self.rmc = ResourceManagementClient(self.credentials, self.subscription_id)

    def _get_credentials(self):
        """Get the necessary credentials for creating the management clients."""
        subscription_id = Secrets.TF_VAR_azure_subscription_id
        credentials = ServicePrincipalCredentials(
            client_id=Secrets.TF_VAR_azure_client_id,
            secret=Secrets.TF_VAR_azure_client_secret,
            tenant=Secrets.TF_VAR_azure_tenant_id
        )
        return credentials, subscription_id
