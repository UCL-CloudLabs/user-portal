# Template secrets file for CloudLabs
#
# This shows what environment variables are needed by the application.
# When running through a WSGI server, the cloudlabs.wsgi launcher imports
# the non-exemplar version of this file to set up the environment.

import os.path

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
