
from flask import Flask

from cloudlabs import (
    context_processors,
    sso,
    views,
    views_host
)
from cloudlabs.admin import views as admin
from cloudlabs.extensions import db, migrate


def create_app(config_name):
    """Build our Flask application with the given config source."""
    app = Flask(__name__)
    app.config.from_object(config_name)
    db.init_app(app)
    migrate.init_app(app, db)
    context_processors.setup(app)
    app.register_blueprint(views.blueprint)
    app.register_blueprint(views_host.blueprint)
    app.register_blueprint(admin.blueprint, url_prefix='/admin')
    sso.setup_login(app)
    return app
