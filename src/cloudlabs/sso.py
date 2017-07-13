from flask import redirect, render_template, session, url_for
from flask_sso import SSO


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
        return {'user': session.get('user', None)}


def setup_shib_login(app):
    """Register a Shibboleth login handler for the given app."""
    ext = SSO(app=app)

    @ext.login_handler
    def login_callback(user_info):
        """Store information in session."""
        session['user'] = user_info
        return redirect(url_for('main.index'))

    @ext.login_error_handler
    def login_error_callback(shib_attrs):
        """Report on a Shibboleth login error."""
        return render_template('login_error.html', shib_attrs=shib_attrs)

    @app.route('/logout')
    def logout():
        session.pop('user')
        return redirect(url_for('main.index'))


def setup_fake_login(app):
    """Setup a fake login handler that always logs in a test user."""
    @app.route('/login')
    def login():
        session['user'] = {
            'eppn': 'userid@ucl.ac.uk',
            'display-name': 'Test User',
            'upi': 'ABCDE12',
            'email': 'first.last@ucl.ac.uk',
        }
        return redirect(url_for('main.index'))

    @app.route('/logout')
    def logout():
        session.pop('user')
        return redirect(url_for('main.index'))
