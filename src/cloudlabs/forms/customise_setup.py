from flask_wtf import FlaskForm
from wtforms.fields import TextAreaField, HiddenField
import wtforms.validators as v


class CustomiseSetupForm(FlaskForm):
    id = HiddenField()
    setup_script = TextAreaField('Setup script',
                                 description='Specify the (bash) script run'
                                             ' to initialise the new host',
                                 validators=[v.Optional()])
