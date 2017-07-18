
from flask import Flask

from cloudlabs import context_processors, sso, views


def create_app(config_name):
    """Build our Flask application with the given config source."""
    app = Flask(__name__)
    app.config.from_object(config_name)
    context_processors.setup(app)
    app.register_blueprint(views.blueprint)
    sso.setup_login(app)
    return app
