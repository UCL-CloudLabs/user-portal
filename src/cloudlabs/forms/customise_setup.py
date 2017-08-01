from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, HiddenField
import wtforms.validators as v


class CustomiseSetup(FlaskForm):
    
    label = HiddenField()
    description = HiddenField()
    dns_name = HiddenField()
    admin_username = HiddenField()
    auth_type = HiddenField()
    admin_ssh_key = HiddenField()
    admin_password = HiddenField()
    git_repo = HiddenField()
    port = HiddenField()
    setup_script = TextAreaField(
    	'Setup script',
        description='Modify the default setup script',
        validators=[v.Optional()])