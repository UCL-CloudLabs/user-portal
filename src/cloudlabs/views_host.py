import logging

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

from .forms.add_host import AddHostForm
from .forms.customise_setup import CustomiseSetupForm
from .host_status import HostStatus
from .models import Host
from .roles import Roles
from .tasks import create_celery
from .utils import login_required, role_required


blueprint = Blueprint('host', __name__)
logger = logging.getLogger("cloudlabs.hosts")
admin_logger = logging.getLogger("cloudlabs.admin")


@blueprint.route('/host/<int:id>')
@login_required
def info(id):
    log_action(id, "view info on")
    host = Host.query.get_or_404(id)
    abort_if_not_owner(host)
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
        for field in ['label', 'base_name', 'description', 'admin_username',
                      'git_repo']:
            fields[field] = form[field].data.strip()
        for field in ['port']:
            fields[field] = form[field].data
        if form.auth_type.data == 'SSH':
            fields['admin_ssh_key_id'] = form.admin_ssh_key.data
        else:
            fields['admin_password'] = form.admin_password.data
        fields['vm_type'] = form.vm_size.data
        if request.form.get('action', None) == 'Customise setup script':
            custom_form = CustomiseSetupForm()
            db_host = Host.create(**fields)
            custom_form.id.data = db_host.id
            custom_form.setup_script.data = db_host.setup_script
            return render_template('setup_script.html', form=custom_form)

        else:
            new_host = Host.create(**fields)
            deploy(new_host)
            return redirect(url_for('main.index'))

    return render_template('add_host.html', form=form)


@blueprint.route('/host/add/customise', methods=('GET', 'POST'))
@role_required(Roles.owner)
def customise_setup():
    form = CustomiseSetupForm()
    if form.validate_on_submit():
        # Save the updated setup script
        host = Host.query.get_or_404(form.id.data)
        abort_if_not_owner(host)
        host.update(setup_script=form.setup_script.data)
        deploy(host)
        flash('Host "{}" added'.format(host.label), 'success')

    return redirect(url_for('main.index'))


@blueprint.route('/host/<int:id>/edit')
@role_required(Roles.owner)
def edit(id):
    log_action(id, "edit")
    host = Host.query.get_or_404(id)
    abort_if_not_owner(host)
    return render_template('not_implemented.html', host=host,
                           thing='Editing hosts')


@blueprint.route('/host/<int:id>/delete')
@role_required(Roles.owner)
def delete(id):
    log_action(id, "delete")
    host = Host.query.get_or_404(id)
    abort_if_not_owner(host)
    label = host.label
    if host.status in [HostStatus.defining]:
        host.delete()
        logger.info("Host %s deleted from database", id)
        flash('Virtual machine "{}" deleted'.format(label), 'success')
    else:
        destroy(host)
    return redirect(url_for('main.index'))


@blueprint.route('/host/<int:id>/control')
@role_required(Roles.owner)
def control(id):
    """Also takes `action` as a query parameter."""
    action = request.args.get('action', '')
    log_action(id, action)
    if action not in {'stop', 'start', 'restart'}:
        flash('Unsupported action "{}"'.format(action), 'error')
        return redirect(url_for('main.index'))
    host = Host.query.get_or_404(id)
    abort_if_not_owner(host)
    if action == 'stop':
        task_id = stop(host)
    elif action == 'start':
        task_id = start(host)
    elif action == 'restart':
        task_id = restart(host)
    log_task(id, action, task_id)
    return redirect(url_for('main.index'))


@blueprint.route('/host/<int:id>/download')
@role_required(Roles.owner)
def download(id):
    log_action(id, "download")
    host = Host.query.get_or_404(id)
    abort_if_not_owner(host)
    return render_template('not_implemented.html', host=host,
                           thing='Downloading host images')


@blueprint.route('/host/<int:id>/view_log')
@role_required(Roles.owner)
def view_log(id):
    log_action(id, "view the log of")
    host = Host.query.get_or_404(id)
    abort_if_not_owner(host)
    return render_template('deploy_log.html', host=host)


def deploy(host):
    """Signals Celery to launch a VM in the background."""
    logger.info("%s asked to deploy new host %s (%s)",
                g.user.ucl_id, host.id, host.base_name)
    host.update(status=HostStatus.deploying)
    celery = create_celery(current_app)
    result = celery.send_task(
        'cloudlabs.deploy',
        args=(host.id,))
    # Record the new deployment so we can keep track of it
    host.update(task=result.id)
    logger.debug("Deployment of host %s has been assigned task %s",
                 host.id, result.id)
    flash('Host "{}" deployment scheduled'.format(host.label), 'success')


def destroy(host):
    """Signals Celery to destroy a VM in the background."""
    if host.status is not HostStatus.destroying:
        celery = create_celery(current_app)
        hard_delete = False
        # First check if the host is currently being deployed, in which case we
        # stop the corresponding task (if already running), and start a "hard"
        # deletion process (interrupting the deployment).
        if host.task:
            hard_delete = True
            logger.info(
                "Deployment of host %s in progress, will revoke task %s.",
                host.id,
                host.task)
            celery.control.revoke(host.task, terminate=True)
        # If the host is in the error state, we will delete its
        # entire resource group directly. This is(?) safer than doing it through
        # Terraform, because the deployment may have stopped at the VM stage,
        # which could(?) cause problems with Terraform.
        if host.status == HostStatus.error:
            hard_delete = True
            logger.info(
                "Host %s was in error state, will delete its whole group.",
                host.id)
        # If the host cannot be found, we check whether its group exists (for
        # example, in case the VM was already deleted from the portal).
        # If the group is not there, we do nothing.
        elif host.status == HostStatus.unknown:
            if not host.group_exists:
                logger.info(
                    "All resources for host %s have been destroyed already.",
                    host.id)
                host.update(status=HostStatus.defining)
                return
            else:
                hard_delete = True
                logger.info("Deleting remaining resource for host %s",
                            host.id)
        # In any other case, we simply delete everything through Terraform.
        host.update(status=HostStatus.destroying)
        logger.info("Sending destroy task for host %s (hard = %s)",
                    host.id, hard_delete)
        celery.send_task(
            'cloudlabs.destroy',
            args=(host.id, hard_delete))
    flash('Host "{}" destruction scheduled'.format(host.label), 'success')


def stop(host):
    """Signals Celery to stop a VM in the background."""
    celery = create_celery(current_app)
    result = celery.send_task(
                'cloudlabs.stop',
                args=(host.id,))
    flash('Host "{}" stopping scheduled'.format(host.label), 'success')
    return result.id


def start(host):
    """Signals Celery to start a VM in the background."""
    celery = create_celery(current_app)
    result = celery.send_task(
                'cloudlabs.start',
                args=(host.id,))
    flash('Host "{}" start scheduled'.format(host.label), 'success')
    return result.id


def restart(host):
    """Signals Celery to restart a VM in the background."""
    celery = create_celery(current_app)
    result = celery.send_task(
                'cloudlabs.restart',
                args=(host.id,))
    flash('Host "{}" restart scheduled'.format(host.label), 'success')
    return result.id


def log_action(host, action):
    logger.info("%s asked to %s host %s", g.user.ucl_id, action, host)


def log_task(host, action, task):
    logger.debug("Task %s has been created to %s host %s", task, action, host)


def abort_if_not_owner(host):
    if g.user is not host.user:
        admin_logger.warning(
            "%s tried to perform an operation on host %d but did not have access",
            g.user.ucl_id,
            host.id)
        abort(404)
