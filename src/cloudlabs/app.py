from flask import Flask
from cloudlabs import views


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_name)
    app.register_blueprint(views.blueprint)
    return app
