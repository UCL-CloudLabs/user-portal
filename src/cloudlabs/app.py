from logging.config import dictConfig

from flask import Flask
import yaml

from cloudlabs import (
    context_processors,
    sso,
    views,
    views_host
)
from cloudlabs.admin import views as admin
from cloudlabs.extensions import db, migrate


def create_app(config_name=None):
    """Build our Flask application with the given config source.

    If no config_name is given, we default to cloudlabs.config.Config,
    unless overridden by the environment variable APP_SETTINGS.
    """
    if config_name is None:
        import os
        config_name = os.getenv('APP_SETTINGS', 'cloudlabs.config.Config')
    app = Flask(__name__)
    app.config.from_object(config_name)
    # Configure logging
    with open(app.config["LOG_CONFIG_FILE"], "r") as config_file:
        config = yaml.safe_load(config_file.read())
    dictConfig(config)
    db.init_app(app)
    migrate.init_app(app, db)
    context_processors.setup(app)
    app.register_blueprint(views.blueprint)
    app.register_blueprint(views_host.blueprint)
    app.register_blueprint(admin.blueprint, url_prefix='/admin')
    sso.setup_login(app)
    return app
