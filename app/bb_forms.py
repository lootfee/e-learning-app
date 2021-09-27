from base64 import b64encode
import jwt
from string import punctuation
from sqlalchemy import func

from app import app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, SelectMultipleField, \
    HiddenField, FileField, MultipleFileField
from wtforms.validators import DataRequired, InputRequired, ValidationError, Email, EqualTo
from flask_wtf.file import FileAllowed
from app.mycaptcha import gen_captcha

from app.models import User


def validate_select(form, field):
    if field.data == 0:
        raise ValidationError("Please select from choice list")


class AddDesignationForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    submit = SubmitField('Submit')


class AddDepartmentForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    submit = SubmitField('Submit')


class AddTopicForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    submit = SubmitField('Submit')


class AddRoleForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    submit = SubmitField('Submit')


class AddUserForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    email = StringField('Email', validators=[Email(), DataRequired()])
    designation = SelectField('Designation', coerce=int, validators=[InputRequired(), validate_select])
    department = SelectField('Department', coerce=int, validators=[InputRequired(), validate_select])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        user = User.query.filter(func.lower(User.email) == email.data.lower().replace(' ', '')).first()
        if user is not None:
            raise ValidationError('Email is already registered!')


class EditUserDesignationForm(FlaskForm):
    # ed_user_id = HiddenField('User Id', validators=[InputRequired()])
    designation = SelectField('Designation', coerce=int, validators=[InputRequired(), validate_select])
    activation = SelectField('Active', coerce=int, validators=[InputRequired()])
    ed_submit = SubmitField('Submit')


class AddBulletinForm(FlaskForm):
    topic = SelectField('Topic', coerce=int, validators=[InputRequired(), validate_select])
    title = StringField('Title', validators=[InputRequired()])
    content = TextAreaField('Content')
    # attachments = MultipleFileField('Upload attachments', validators=[FileAllowed(['pdf', 'jpg', 'png', 'mp4'], 'PDF, Images and Videos only')])
    important = BooleanField('Important')
    departments = SelectField('Departments', coerce=int, validators=[InputRequired()])
    designations = SelectField('Designations', coerce=int, validators=[InputRequired()])
    # department_list = HiddenField('Departments List')
    # designation_list = HiddenField('Designations List')
    submit = SubmitField('Submit')
    save = SubmitField('Save')
    add_attachment = SubmitField('Add attachment')


class EditBulletinForm(FlaskForm):
    topic = SelectField('Topic', coerce=int, validators=[InputRequired(), validate_select])
    title = StringField('Title', validators=[InputRequired()])
    content = TextAreaField('Content')
    # attachments = MultipleFileField('Upload attachments', validators=[FileAllowed(['pdf', 'jpg', 'png', 'mp4'], 'PDF, Images and Videos only')])
    important = BooleanField('Important')
    departments = SelectField('Departments', coerce=int, validators=[InputRequired()])
    designations = SelectField('Designations', coerce=int, validators=[InputRequired()])
    submit = SubmitField('Submit')
    save = SubmitField('Save')


class CommentForm(FlaskForm):
    comment = TextAreaField('Comment:')
    submit = SubmitField('Submit')