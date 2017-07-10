from flask import Flask

from cloudlabs import sso, views


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_name)
    app.register_blueprint(views.blueprint)
    sso.setup_login(app)
    return app
