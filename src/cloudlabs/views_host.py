
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from .deployer.deployer import Deployer
from .forms.add_host import AddHostForm
from .models import Host
from .utils import login_required


blueprint = Blueprint('host', __name__)


@blueprint.route('/host/<int:id>')
@login_required
def info(id):
    host = Host.query.get_or_404(id)
    return render_template('host_info.html', host=host)


@blueprint.route('/host/add', methods=('GET', 'POST'))
@login_required
def add():
    form = AddHostForm()
    # Fill in options for SSH key
    form.admin_ssh_key.choices = [(key.id, key.label)
                                  for key in g.user.ssh_keys]
    if form.validate_on_submit():
        fields = {
            'user_id': g.user.id,
        }
        for field in ['label', 'dns_name', 'description', 'admin_username',
                      'git_repo']:
            fields[field] = form[field].data.strip()
        for field in ['port']:
            fields[field] = form[field].data
        if form.auth_type.data == 'SSH':
            fields['admin_ssh_key_id'] = form.admin_ssh_key.data
        else:
            fields['admin_password'] = form.admin_password.data
        new_host = Host.create(**fields)
        deploy(new_host)
        flash('Host "{}" added'.format(form.label.data), 'success')
        return redirect(url_for('main.index'))
    return render_template('add_host.html', form=form)


@blueprint.route('/host/<int:id>/edit')
@login_required
def edit(id):
    host = Host.query.get_or_404(id)
    return render_template('not_implemented.html', host=host,
                           thing='Editing hosts')


@blueprint.route('/host/<int:id>/delete')
@login_required
def delete(id):
    host = Host.query.get_or_404(id)
    if host.user is not g.user:
        abort(404)
    label = host.label
    host.delete()
    flash('Virtual machine "{}" deleted'.format(label), 'success')
    return redirect(url_for('main.index'))


@blueprint.route('/host/<int:id>/control')
@login_required
def control(id):
    """Also takes `action` as a query parameter."""
    action = request.args.get('action', '')
    if action not in {'stop', 'start', 'restart'}:
        flash('Unsupported action "{}"'.format(action), 'error')
        return redirect(url_for('main.index'))
    host = Host.query.get_or_404(id)
    return render_template('not_implemented.html', host=host,
                           thing='Running hosts')


@blueprint.route('/host/<int:id>/download')
@login_required
def download(id):
    host = Host.query.get_or_404(id)
    return render_template('not_implemented.html', host=host,
                           thing='Downloading host images')


def deploy(host):
    """Calls deployer to launch a VM.

    If successful, adds the Terraform state file to the DB.
    """
    deployer = Deployer(current_app.root_path)
    deployer.deploy(host)

    # host.terraform_state = render_template('state.json', host=host)
    # host.save()
