from enum import Enum


class HostStatus(Enum):
    """Possible statuses for CloudLabs hosts."""
    defining = 'Defining'    # Not yet started to deploy
    deploying = 'Deploying'  # Deployment in progress
    starting = 'Starting'    # Machine is spinning up; service not live
    running = 'Running'      # Web app is running
    stopped = 'Stopped'      # Machine deployed but not turned on
    destroying = 'Destroying'
    error = 'Failed to deploy'

def get_status_azure(host):
    """Return the status of a host deployed on Azure."""
    # TODO Get the name of the VM and resource group, and use the ComputeManager
    # to retrieve the status. This is a placeholder while the naming becomes
    # stable.
    # Something like this:
    #stat = cm.virtual_machines.get(vm_name, group_name).instance_view.statuses
    return HostStatus.error
