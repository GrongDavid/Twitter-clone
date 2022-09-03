from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, TextAreaField
from wtforms.validators import DataRequired, Email, Length 


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    image_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class UpdateForm(FlaskForm):
    """Update user form"""

    username = StringField('Edit username', validators=[DataRequired()])
    email = StringField('Edit E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Edit password', validators=[Length(min=6)])
    image_url = StringField('Edit profile image')
    header_image_url = StringField('Edit header image')
    bio = TextAreaField('Edit Bio', validators=[Length(max=160)])

