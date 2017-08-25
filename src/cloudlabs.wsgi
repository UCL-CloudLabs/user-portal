import os
import sys

our_folder = os.path.dirname(__file__)
sys.path.insert(0, our_folder)

# Set the secrets as environment variables
import secrets
for name in dir(secrets):
    if name and name[0] != '_' and isinstance(getattr(secrets, name), str):
        os.environ[name] = getattr(secrets, name)

from autoapp import app as application
