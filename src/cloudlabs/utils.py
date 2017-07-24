from functools import wraps
from flask import g, redirect, request, session, url_for

from .models import User


def login_required(view):
    """Decorator for views that ensures only logged-in users can see them."""
    @wraps(view)
    def decorated_view(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', target=request.url))
        setup_user()
        return view(*args, **kwargs)
    return decorated_view


def setup_user(user_info=None):
    """Sets up a user object based on info from the login system or session."""
    if user_info is None:
        # Try to find user info from the session
        user_info = session.get('user', None)
    else:
        session['user'] = user_info
    if not user_info:
        g.user = None
    else:
        kwargs = {field: user_info[field] for field in ['eppn', 'email', 'name', 'upi']}
        g.user = User.get_or_create(**kwargs)
    return g.user
