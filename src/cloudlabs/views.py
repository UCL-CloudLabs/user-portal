
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
)


blueprint = Blueprint('main', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')


@blueprint.context_processor
def inject_now():
    """Enable {{now}} in templates, used by the footer."""
    return {'now': datetime.utcnow()}


@blueprint.route('/profile')
def profile():
    return ''
