import re
import uuid

from haikunator import Haikunator

"""
Useful methods for generating acceptable names for hosts, as well as for the
associated resources.
"""


def create_host_name(base_name):
    """Return a domain name that is likely to be unique."""
    clean_name = 'ucl' + re.sub(r'[^a-zA-Z0-9]', '', base_name)
    # Append a random adjective, noun and 4-digit hex token
    return clean_name + Haikunator().haikunate(delimiter='', token_hex=True)


def resource_names(host):
    """Generate names for cloud resources for the given host.

    A deployed host requires various resources alongside the bare VM, such
    as networking, storage, containers, etc. Different providers have
    different constraints on these names, so we don't want to hardcode this
    within the Host class. Instead this method returns a dictionary with
    suitable names based on a given host configuration, providing a hook to
    abstract provider requirements.

    The resulting dictionary is designed to be passed as the 'names'
    parameter to the Terraform template in self._render.
    """
    # Assuming all Azure for now
    base_name = host.dns_name
    return {
        'resource_group': base_name + 'rg',
        'dns_name': base_name,
        'storage': uuid.uuid5(uuid.NAMESPACE_DNS, host.basic_url).hex[:24],
        'vm': 'virtual_machine',
    }


def group_name(host):
    """Get the resource group corresponding to a host, according to its name."""
    return host.dns_name + 'rg'


def vm_name(host):
    """
    Get the name of the machine resource corresponding to a host.
    Since it's unique across the resource group, and Azure imposes restrictions
    on the VM name length which haikunator might break, we can hardcode it.
    """
    return 'virtual_machine'


def azure_url(dns_name):
    """Return the full URL of a VM hosted on Azure given its DNS name."""
    return '{}.uksouth.cloudapp.azure.com'.format(dns_name)
