
from flask import (
    Blueprint,
    render_template,
)
from .models import Host, SshKey, User


blueprint = Blueprint('host', __name__)


@blueprint.route('/host/<int:id>')
def info(id):
    return ''


@blueprint.route('/host/add')
def add():
    return ''


@blueprint.route('/host/<int:id>/edit')
def edit(id):
    return ''


@blueprint.route('/host/<int:id>/delete')
def delete(id):
    return ''


@blueprint.route('/host/<int:id>/control')
def control(id):
    """Also takes `action` as a query parameter."""
    return ''


@blueprint.route('/host/<int:id>/download')
def download(id):
    return ''
