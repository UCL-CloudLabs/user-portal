from enum import Enum


class Roles(Enum):
    """Possible roles for CloudLabs users."""
    admin = 'Admin'
    owner = 'Owner'  # Able to create & manage hosts
