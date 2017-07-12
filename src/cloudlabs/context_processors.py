from datetime import datetime

def setup(app):
    """Define context processors for the given app."""

    @app.context_processor
    def inject_now():
        """Enable {{now}} in templates, used by the footer."""
        return {'now': datetime.utcnow()}
