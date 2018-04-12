
from flask import (
    abort,
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    url_for,
)
from .forms.add_key import AddKeyForm
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


@blueprint.route('/data_info')
def data_info():
    """Show a confirmation page with information on data-related limitations."""
    return render_template('data_info.html')


@blueprint.route('/keys/add', methods=('GET', 'POST'))
@login_required
def add_key():
    form = AddKeyForm()
    if form.validate_on_submit():
        SshKey.create(
            user_id=g.user.id,
            label=form.label.data.strip(),
            public_key=form.public_key.data.strip())
        flash('SSH key "{}" added'.format(form.label.data), 'success')
        return redirect(url_for('main.profile'))
    return render_template('add_key.html', form=form)


@blueprint.route('/keys/<int:id>/delete')
@login_required
def delete_key(id):
    key = SshKey.query.get_or_404(id)
    if key.user is not g.user:
        abort(404)
    label = key.label
    key.delete()
    flash('SSH key "{}" deleted'.format(label), 'success')
    return redirect(url_for('main.profile'))
