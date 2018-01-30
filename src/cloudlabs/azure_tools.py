"""Miscelanneous methods for working with Azure."""

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient

from .secrets import Secrets


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


def get_compute_manager(credentials=None, subscription_id=None):
    """Get an instance of an Azure ComputeManagementClient."""
    if not (credentials and subscription_id):
        credentials, subscription_id = get_credentials()
    cmc = ComputeManagementClient(credentials, subscription_id)
    return cmc


def get_resource_manager(credentials=None, subscription_id=None):
    """Get an instance of an Azure ResourceManagementClient."""
    if not (credentials and subscription_id):
        credentials, subscription_id = get_credentials()
    rmc = ResourceManagementClient(credentials, subscription_id)
    return rmc
