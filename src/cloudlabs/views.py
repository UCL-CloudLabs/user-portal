
from flask import (
    Blueprint,
    g,
    redirect,
    render_template,
    url_for,
)
from .models import SshKey
from .utils import login_required


blueprint = Blueprint('main', __name__)


@blueprint.route('/')
def index():
    return render_template('index.html')


@blueprint.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@blueprint.route('/keys/add', methods=('GET', 'POST'))
@login_required
def add_key():
    return ''


@blueprint.route('/keys/<int:id>/delete')
@login_required
def delete_key(id):
    return ''
