# Template secrets file for CloudLabs
#
# This shows what environment variables are needed by the application.
# Copy this as secrets.py and fill in suitable values for your system.

import os
import os.path


class Secrets:
    # The Flask secret key
    CLOUDLABS_SECRET_KEY = ""

    # Path to the SSH private key to use when logging in to deployed hosts.
    # The corresponding public key (which will be coped to each new host) is
    # expected to live at the same path with a .pub extension.
    PRIVATE_SSH_KEY_PATH = os.path.expanduser("~/.ssh/id_rsa_cloudlabs_dev")

    # Details of our Azure subscription, used by Terraform
    TF_VAR_azure_tenant_id = ""
    TF_VAR_azure_client_id = ""
    TF_VAR_azure_client_secret = ""
    TF_VAR_azure_subscription_id = ""


def apply_secrets():
    """Place all the secrets in environment variables."""
    for name, value in Secrets.__dict__.items():
        if name[0] != '_':
            os.environ[name] = value
