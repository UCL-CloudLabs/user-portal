import time

import pytest

from cloudlabs.azure_tools import AzureTools, _parse_statuses
from cloudlabs.host_status import HostStatus
from cloudlabs.secrets import Secrets

# Example of status codes returned by the Azure API:
input_statuses = [
    ['ProvisioningState/updating', 'PowerState/starting'],
    ['ProvisioningState/succeeded', 'PowerState/running'],
    ['ProvisioningState/succeeded', 'PowerState/deallocated'],
    ['ProvisioningState/updating', 'PowerState/stopping'],
    ['ProvisioningState/succeeded', 'PowerState/stopped'],
    ['ProvisioningState/updating', 'PowerState/deallocating'],
    ['ProvisioningState/deleting']
]
# And the corresponding statuses we want them to map to:
output_statuses = [
    HostStatus.starting,
    HostStatus.running,
    HostStatus.stopped,
    HostStatus.stopping,
    HostStatus.stopping,  # stopped but not deallocated yet
    HostStatus.stopping,
    HostStatus.destroying
]


@pytest.mark.offline
@pytest.mark.parametrize("statuses,result", zip(input_statuses, output_statuses))
def test_parse_statuses(statuses, result):
    """Test that a VM's status as retrieved from Azure is correctly interpreted."""
    assert _parse_statuses(statuses) == result


@pytest.fixture()
def host(image):
    """Mock a DB entry (Host) backed by a real VM to use with AzureTools."""
    class MockHost():
        def __init__(self, dns_name):
            self.id = 42
            self.dns_name = dns_name
            # self.status = HostStatus.running
    return MockHost(image)


@pytest.fixture
def image():
    """An Azure VM created from an existing image."""
    # Using Azure CLI:
    # az vm create --name ANewVM --resource-group testImage_rg --image testImage
    # but it looks like anyone can connect to it?
    tools = AzureTools()
    info = {
        'subscription_id': Secrets.TF_VAR_azure_subscription_id,
        'rg': 'testImage_rg',
        'image': 'testImage',
        'nic': 'test_ni'
    }
    vm_parameters = {
        'storage_profile': {
            # TODO: Can we also include a reference to a disk here? This will
            # save us having to create/destroy a disk to go along with the VM.
            # See the example at:
            # https://docs.microsoft.com/en-gb/rest/api/compute/virtualmachines/createorupdate#create_a_platform-image_vm_with_unmanaged_os_and_data_disks
            'image_reference': {
                'id': '/subscriptions/{subscription_id}/resourceGroups/{rg}/providers/Microsoft.Compute/images/{image}'.format(**info)
            },
        },
        'hardware_profile': {
            'vm_size': 'Standard_A6'
        },
        'network_profile': {
            'network_interfaces': [
                {
                    'id': '/subscriptions/{subscription_id}/resourceGroups/{rg}/providers/Microsoft.Network/networkInterfaces/{nic}'.format(**info),
                    'primary': True
                }
            ]
        },
        # It seems we need these?
        'os_profile': {
            'admin_username': 'cloudlabs',
            'admin_password': 'Password1234!',
            'computer_name': 'mycomputer'
        },
        'location': 'ukwest'
    }
    # TODO: Create into a different, randomly-named group. This will allow
    # multiple tests to be running in parallel, but would require us to create a
    # dedicated NIC (each NIC can only be attached to one VM). On the other hand,
    # it would simplify the tear-down process, as we could just delete the new
    # resource group.
    # Update: This is complex to do as the configuration quickly becomes too long.
    target_rg = info["rg"]
    target_vm = "testImage_vm"
    action = tools.cmc.virtual_machines.create_or_update(
                target_rg, target_vm, vm_parameters)
    action.wait()
    # Wait a bit to ensure machine is up and running, because sometimes the VM's
    # status is still "Starting" when the above action completes.
    time.sleep(30)
    print("Created VM from image")
    yield "testImage_"  # the prefix of the resource group and VM name
    print("Destroying resources created")
    # Destroy the new VM
    disk = tools.cmc.virtual_machines.instance_view(target_rg, target_vm).disks[0]
    action = tools.cmc.virtual_machines.delete(target_rg, target_vm)
    action.wait()
    # Destroy the OS disk that was created with the VM
    action = tools.cmc.disks.delete(target_rg, disk.name)
    action.wait()


def test_azure_action_sequence(host):
    """Test that the AzureTools methods drive a VM through the right states."""
    # Set up test by starting an existing VM
    tools = AzureTools()
    # The machine is running when first started, but let's check anyway.
    assert tools.get_status(host) == HostStatus.running, \
        "Host status should be running"
    # Restart the VM and check that it worked
    tools.restart_VM(host)
    assert tools.get_status(host) == HostStatus.running, \
        "Host status should be running"
    # The above is a bit sketchy, since we don't see whether the VM was actually
    # restarted or whether the action had no effect. I'm not sure what else we
    # can do, however.
    # Stop the VM and check that it worked
    tools.stop_VM(host)
    assert tools.get_status(host) == HostStatus.stopped, \
        "Host status should be stopped"
    # Start the VM and check that it worked
    tools.start_VM(host)
    assert tools.get_status(host) == HostStatus.running, \
        "Host status should be running"
