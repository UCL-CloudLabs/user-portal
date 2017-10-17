from enum import Enum


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
    # TODO Get the name of the VM and resource group, and use the ComputeManager
    # to retrieve the status. This is a placeholder while the naming becomes
    # stable.
    # Something like this:
    statuses = cm.virtual_machines.instance_view(group_name, vm_name).statuses
    prov_status = get_provisioning_status(host)
    if prov_status == "deleting":
        return HostStatus.destroying
    else:
        for status in statuses:
            power_status = _remove_prefix(status, "PowerStatus/")
            if power_status == "deallocated" or power_status == "stopped":
                return HostStatus.stopped
            elif power_status == "starting":
                return HostStatus.starting
            elif power_status == "running":
                return HostStatus.running
            elif power_status == "deallocating" or power_status == "stopping":
                return HostStatus.stopping
        return HostStatus.error #  uknown status, return error


def get_provisioning_status_azure(host):
    #statuses = cm.virtual_machines.instance_view(group_name, vm_name).statuses
    for status in statuses:
        if status.code.startswith("ProvisioningState/"):
            return _remove_prefix(status, "ProvisioningState/")
    assert False  # should never happen
    return None


def _remove_prefix(string, prefix):
    # inspired from
    # https://stackoverflow.com/questions/16891340/remove-a-prefix-from-a-string
    # but maybe we don't need it
    return string[len(prefix):] if string.startswith(prefix) else string
