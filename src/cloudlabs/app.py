from logging.config import dictConfig
from os.path import expanduser

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
        # The app may be launched by a different user (usually if running on
        # a server), but the configuration file cannot know that in advance.
        # It therefore uses "~" to refer to the user's home directory, which
        # we have to replace with the actual path, as the dictConfig method
        # will just use the path passed to it without doing any substitutions.
        # This currently only affects the "production" configuration, as in
        # the DevConfig the logging file is local to where to the code is
        # launched from (without using "~").
        filename = config["handlers"]["file_handler"]["filename"]
        config["handlers"]["file_handler"]["filename"] = expanduser(filename)
    dictConfig(config)
    db.init_app(app)
    migrate.init_app(app, db)
    context_processors.setup(app)
    app.register_blueprint(views.blueprint)
    app.register_blueprint(views_host.blueprint)
    app.register_blueprint(admin.blueprint, url_prefix='/admin')
    sso.setup_login(app)
    return app
