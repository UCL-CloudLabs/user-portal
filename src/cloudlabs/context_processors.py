from datetime import datetime


def setup(app):
    """Define context processors for the given app."""
    @app.context_processor
    def inject_now():
        """Enable {{now}} in templates, used by the footer."""
        return {'now': datetime.utcnow()}

    @app.context_processor
    def inject_roles():
        """Provide the Roles enum to all templates."""
        from .roles import Roles
        return {'Roles': Roles}

    @app.context_processor
    def inject_status():
        """Provide the HostStatus enum to all templates."""
        from .host_status import HostStatus
        return {'HostStatus': HostStatus}
