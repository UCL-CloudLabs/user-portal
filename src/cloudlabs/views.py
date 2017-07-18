
from flask import (
    Blueprint,
    render_template,
)
from .models import Host, SshKey, User


blueprint = Blueprint('main', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')


@blueprint.route('/profile')
def profile():
    return ''
