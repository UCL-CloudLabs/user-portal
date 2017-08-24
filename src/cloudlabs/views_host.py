
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
from .forms.customise_setup import CustomiseSetupForm
from .models import Host
from .roles import Roles
from .utils import login_required, role_required


blueprint = Blueprint('host', __name__)


@blueprint.route('/host/<int:id>')
@login_required
def info(id):
    host = Host.query.get_or_404(id)
    return render_template('host_info.html', host=host)


@blueprint.route('/host/add', methods=('GET', 'POST'))
@role_required(Roles.owner)
def add():
    form = AddHostForm()
    # Fill in options for SSH key
    form.admin_ssh_key.choices = [(key.id, key.label)
                                  for key in g.user.ssh_keys]
    if form.validate_on_submit():
        fields = {'user_id': g.user.id}
        for field in ['label', 'dns_name', 'description', 'admin_username',
                      'git_repo']:
            fields[field] = form[field].data.strip()
        for field in ['port']:
            fields[field] = form[field].data
        if form.auth_type.data == 'SSH':
            fields['admin_ssh_key_id'] = form.admin_ssh_key.data
        else:
            fields['admin_password'] = form.admin_password.data
        if request.form.get('action', None) == 'Customise setup script':
            custom_form = CustomiseSetupForm()
            db_host = Host.create(**fields)
            custom_form.id.data = db_host.id
            custom_form.setup_script.data = db_host.setup_script
            return render_template('setup_script.html', form=custom_form)

        else:
            new_host = Host.create(**fields)
            deploy(new_host)
            flash('Host "{}" added'.format(form.label.data), 'success')
            return redirect(url_for('main.index'))

    return render_template('add_host.html', form=form)


@blueprint.route('/host/add/customise', methods=('GET', 'POST'))
@role_required(Roles.owner)
def customise_setup():
    form = CustomiseSetupForm()
    if form.validate_on_submit():
        # Save the updated setup script
        host = Host.query.get_or_404(form.id.data)
        host.update(setup_script=form.setup_script.data)
        deploy(host)
        flash('Host "{}" added'.format(host.label), 'success')

    return redirect(url_for('main.index'))


@blueprint.route('/host/<int:id>/edit')
@role_required(Roles.owner)
def edit(id):
    host = Host.query.get_or_404(id)
    return render_template('not_implemented.html', host=host,
                           thing='Editing hosts')


@blueprint.route('/host/<int:id>/delete')
@role_required(Roles.owner)
def delete(id):
    host = Host.query.get_or_404(id)
    if host.user is not g.user:
        abort(404)
    label = host.label
    host.delete()
    flash('Virtual machine "{}" deleted'.format(label), 'success')
    return redirect(url_for('main.index'))


@blueprint.route('/host/<int:id>/control')
@role_required(Roles.owner)
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
@role_required(Roles.owner)
def download(id):
    host = Host.query.get_or_404(id)
    return render_template('not_implemented.html', host=host,
                           thing='Downloading host images')


@blueprint.route('/host/<int:id>/view_log')
@role_required(Roles.owner)
def view_log(id):
    host = Host.query.get_or_404(id)
    return render_template('deploy_log.html', host=host)


def deploy(host):
    """Calls deployer to launch a VM.

    If successful, adds the Terraform state file to the DB.
    """
    deployer = Deployer(current_app.root_path)
    deployer.deploy(host)

    # host.terraform_state = render_template('state.json', host=host)
    # host.save()
