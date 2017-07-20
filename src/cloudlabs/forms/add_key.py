from flask import g
from flask_wtf import FlaskForm
from wtforms.fields import StringField, TextAreaField
import wtforms.validators as v

from ..models import SshKey


class AddKeyForm(FlaskForm):
    """Form for adding a new SSH public key."""
    label = StringField('Label', validators=[v.Length(min=2, max=SshKey.label.type.length)])
    public_key = TextAreaField('Public key', validators=[v.DataRequired()])

    def validate_label(form, field):
        """Check a user doesn't duplicate labels."""
        existing_labels = [key.label for key in g.user.ssh_keys]
        if field.data.strip() in existing_labels:
            raise v.ValidationError('You must choose a unique label for each key')
