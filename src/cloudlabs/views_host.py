
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from .forms.add_host import AddHostForm
from .models import Host, SshKey, User
from .utils import login_required


blueprint = Blueprint('host', __name__)


@blueprint.route('/host/<int:id>')
def info(id):
    return ''


@blueprint.route('/host/add', methods=('GET', 'POST'))
@login_required
def add():
    form = AddHostForm()
    # Fill in options for SSH key
    form.admin_ssh_key.choices = [(key.id, key.label) for key in g.user.ssh_keys]
    if form.validate_on_submit():
        fields = {
            'user_id': g.user.id,
        }
        for field in ['label', 'dns_name', 'description', 'admin_username']:
            fields[field] = form[field].data.strip()
        if form.auth_type.data == 'SSH':
            fields['admin_ssh_key_id'] = form.admin_ssh_key.data
        else:
            fields['admin_password'] = form.admin_password.data
        # TODO: Creation script in fake Terraform state
        Host.create(**fields)
        flash('Host "{}" added'.format(form.label.data), 'success')
        return redirect(url_for('main.index'))
    return render_template('add_host.html', form=form)


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
