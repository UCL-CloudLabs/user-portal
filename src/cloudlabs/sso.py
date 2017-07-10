from flask import session
from flask_sso import SSO


def setup_login(app):
    """Register a Shibboleth login handler for the given app."""
    ext = SSO(app=app)

    @ext.login_handler
    def login_callback(user_info):
        """Store information in session."""
        session['user'] = user_info
