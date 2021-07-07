from base64 import b64encode
import jwt
from string import punctuation
from sqlalchemy import func

from app import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, InputRequired, ValidationError, Email, EqualTo
from app.mycaptcha import gen_captcha

from app.models import User


def validate_select(form, field):
    if field.data == 0:
        raise ValidationError("Please select from choice list")


class AddDesignationForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    submit = SubmitField('Submit')


class AddUserForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    email = StringField('Email', validators=[Email(), DataRequired()])
    designation = SelectField('Designation', coerce=int, validators=[InputRequired(), validate_select])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        user = User.query.filter(func.lower(User.email) == email.data.lower().replace(' ', '')).first()
        if user is not None:
            raise ValidationError('Email is already registered!')


class EditUserDesignationForm(FlaskForm):
    ed_user_id = HiddenField('User Id', validators=[InputRequired()])
    ed_designation = SelectField('Designation', coerce=int, validators=[InputRequired(), validate_select])
    ed_submit = SubmitField('Submit')