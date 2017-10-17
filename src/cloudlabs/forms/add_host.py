from flask import g
from flask_wtf import FlaskForm
from wtforms.fields import (
    IntegerField,
    SelectField,
    StringField,
    TextAreaField
)
import wtforms.validators as v

from ..models import Host, SshKey


class AddHostForm(FlaskForm):
    """Form for adding a new virtual host."""

    label = StringField(
        'Label',
        description='A short label for you to identify this host easily',
        validators=[v.Length(min=2, max=Host.label.type.length)])

    description = TextAreaField(
        'Description',
        description='A longer description of the host, purely for your own '
                    'benefit',
        validators=[v.Optional()])

    base_name = StringField(
        'URL',
        description='The canonical DNS name for this host, which must be '
                    'globally unique. Note that the .cloudlabs.rc.ucl.ac.uk '
                    'suffix will be added automatically, and should not be '
                    'included here.',
        validators=[v.Length(min=1, max=Host.dns_name.type.length)])
    # TODO adapt max length to exclude suffixes/randomisation?

    admin_username = StringField(
        'Admin username',
        description='Username of the admin user to be created on the new host',
        validators=[v.Length(min=1, max=Host.admin_username.type.length)])

    auth_type = SelectField(
        'Authentication type',
        description='How the admin user should be authenticated when logging '
                    'in via SSH',
        choices=[('SSH', 'SSH public key'), ('Password', 'Password')])

    admin_ssh_key = SelectField(
        'SSH public key',
        description='Which of your pre-configured SSH public keys to use for '
                    'logging in.'
        ' Set up further keys by visiting your profile page.',
        coerce=int)

    admin_password = StringField(
        'Admin password',
        description='Password to use for the admin user on this host',
        validators=[v.Optional(), v.Length(min=12,
                                           max=Host.admin_password.type.length
                                           )])

    git_repo = StringField(
        'Git repository',
        description='Location of the git repository to clone on the new host.'
        ' It is assumed to contain a Dockerfile that will be built,'
        ' although this can be customised.',
        validators=[v.Length(min=1, max=Host.git_repo.type.length)])

    port = IntegerField(
        'Port',
        description='Which port the web application should be exposed on.'
        ' This is used to generate our default installation script,'
        ' which can be customised if needed.',
        default=80,
        validators=[v.NumberRange(min=1, max=65535)])

    def validate_label(form, field):
        """Check a user doesn't duplicate labels."""
        label = field.data.strip()
        if Host.query.filter_by(user_id=g.user.id, label=label).count() > 0:
            raise v.ValidationError('You must choose a unique label for each '
                                    'host')

    def validate_dns_name(form, field):
        """DNS names must be globally unique."""
        dns_name = field.data.strip()
        if Host.query.filter_by(dns_name=dns_name).count() > 0:
            raise v.ValidationError('The URL {} has already '
                                    'been taken'.format(dns_name))

    def validate_admin_ssh_key(form, field):
        """The user must pick one of their keys."""
        key_id = field.data
        if key_id and SshKey.query.filter_by(user_id=g.user.id,
                                             id=key_id).count() == 0:
            raise v.ValidationError(
                        'You must select one of your pre-configured SSH keys')
