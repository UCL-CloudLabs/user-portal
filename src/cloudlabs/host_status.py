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
    unknown = 'Not found'    # Machine not found on the cloud
