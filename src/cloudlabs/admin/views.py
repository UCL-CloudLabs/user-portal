
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

from ..models import User
from ..roles import Roles
from ..utils import role_required


blueprint = Blueprint('admin', __name__, template_folder='templates')


@blueprint.route('/')
@role_required(role=Roles.admin)
def index():
    return render_template('admin/index.html',
                           all_users=User.query.order_by('name').all())


@blueprint.route('/user')
@role_required(role=Roles.admin)
def user():
    """Takes user and change as query parameters."""
    user = User.query.get_or_404(request.args.get('user', ''))
    change = request.args.get('change', '')
    if not isinstance(change, str) or not change or change[0] not in '+-':
        abort(400)
    try:
        role = getattr(Roles, change[1:])
    except AttributeError:
        abort(400)
    if change[0] == '+':
        # Add new role
        user.roles.add(role)
        user.save()
        current_app.logger.info("An admin (%s) has given role '%s' to user %s",
                                g.user.ucl_id, role.value, user.ucl_id)
        flash('Role {} added for {}'.format(role.value, user.name), 'success')
    else:
        # Remove existing role
        try:
            user.roles.remove(role)
            user.save()
            current_app.logger.info("An admin (%s) has removed role '%s' from user %s",
                                    g.user.ucl_id, role.value, user.ucl_id)
            flash('Role {} removed from {}'.format(role.value, user.name), 'success')
        except KeyError:
            flash('User {} does not have role {}'.format(user.name, role.value), 'error')
    return redirect(url_for('admin.index'))
