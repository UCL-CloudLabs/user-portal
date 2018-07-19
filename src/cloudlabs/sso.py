import logging

from flask import redirect, render_template, request, session, url_for
from flask_sso import SSO

from .roles import Roles
from .utils import setup_user


logger = logging.getLogger("cloudlabs.admin")


def setup_login(app):
    """Register a login handler for the given app.

    If in development mode, will register a fake handler that always logs in
    a test user. Otherwise uses Flask-SSO to login with Shibboleth.
    """
    if app.config['DEVELOPMENT']:
        setup_fake_login(app)
    else:
        setup_shib_login(app)

    @app.context_processor
    def inject_user():
        return {'user': setup_user()}


def setup_shib_login(app):
    """Register a Shibboleth login handler for the given app."""
    ext = SSO(app=app)

    @ext.login_handler
    def login_callback(user_info):
        """Store information in session."""
        setup_user(user_info)
        target = request.args.get('target', url_for('main.index'))
        return redirect(target)

    @ext.login_error_handler
    def login_error_callback(shib_attrs):
        """Report on a Shibboleth login error."""
        logger.error(
            "Shibboleth login encountered an error. This is the information received:\n"
            + "Shibboleth:\n"
            + ", ".join("{}={}".format(attr, value) for attr, value in shib_attrs.items())
            + "\nServer:\n"
            + ", ".join("{}={}".format(attr, value) for attr, value in request.environ.items())
        )
        return render_template('login_error.html', shib_attrs=shib_attrs)

    @app.route('/logout')
    def logout():
        session.pop('user')
        return redirect(url_for('main.index'))


def setup_fake_login(app):
    """Setup a fake login handler that always logs in a test user."""
    @app.route('/login')
    def login():
        user = setup_user({
            'eppn': 'userid@ucl.ac.uk',
            'name': 'Test User',
            'upi': 'ABCDE12',
            'email': 'first.last@ucl.ac.uk',
        })
        user.roles.add(Roles.admin)
        target = request.args.get('target', url_for('main.index'))
        return redirect(target)

    @app.route('/logout')
    def logout():
        session.pop('user')
        return redirect(url_for('main.index'))
