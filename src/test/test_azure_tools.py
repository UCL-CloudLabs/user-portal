import pytest

from cloudlabs.azure_tools import AzureTools, _parse_statuses
from cloudlabs.host_status import HostStatus

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


@pytest.mark.parametrize("statuses,result", zip(input_statuses, output_statuses))
def test_parse_statuses(statuses, result):
    """Test that a VM's status as retrieved from Azure is correctly interpreted."""
    assert _parse_statuses(statuses) == result


@pytest.fixture(scope="module")
def host():
    """Mock a DB entry (Host) to use with AzureTools."""
    class MockHost():
        def __init__(self, dns_name):
            self.dns_name = dns_name
    return MockHost("")


@pytest.fixture
def image():
    # create the machine
    vm = None

    def tear_down():
        pass
    vm.addfinalizer(tear_down)
    return vm


def test_azure_action_sequence(image, host):
    """Test that the AzureTools methods drive a VM through the right states."""
    # Set up test by starting an existing VM
    tools = AzureTools()
    tools.start_VM(host)
    assert tools.get_status(host) == HostStatus.running, \
        "Host status should be running"
    tools.restart_VM(host)
    assert tools.get_status(host) == HostStatus.running, \
        "Host status should be running"
    tools.stop_VM(host)
    assert tools.get_status(host) == HostStatus.stopped, \
        "Host status should be stopped"
