from cloudlabs.app import create_app
from cloudlabs.secrets import apply_secrets


apply_secrets()
app = create_app()
