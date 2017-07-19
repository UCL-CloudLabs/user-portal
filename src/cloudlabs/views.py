
from flask import (
    Blueprint,
    render_template,
)
from .models import SshKey, User


blueprint = Blueprint('main', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')


@blueprint.route('/profile')
def profile():
    return render_template('profile.html')


@blueprint.route('/keys/add')
def add_key():
    return ''


@blueprint.route('/keys/<int:id>/delete')
def delete_key(id):
    return ''
