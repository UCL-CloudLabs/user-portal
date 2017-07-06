import os
from cloudlabs.app import create_app

app = create_app(
    os.getenv('APP_SETTINGS', 'reporting.config.Config'))
