import pytest

from cloudlabs.azure_tools import _parse_statuses
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
