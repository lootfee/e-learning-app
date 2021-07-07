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


class RegistrationForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'autocomplete': 'off'})
    # area = SelectField('Area', coerce=int, validators=[DataRequired(), validate_select])
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'autocomplete': 'off'})
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')], render_kw={'autocomplete': 'off'})
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter(func.lower(User.email) == email.data.lower().replace(' ', '')).first()
        if user is not None:
            raise ValidationError('Email is already registered!')

    def validate_password(self, password):
        passwd = password.data
        spec_char = set(punctuation)

        if len(passwd) < 8:
            raise ValidationError('Password length should be at least 8 characters!')

        if len(passwd) > 50:
            raise ValidationError('Password length should be greater than 50 characters!')

        if not any(char.isdigit() for char in passwd):
            raise ValidationError('Password should have at least one number!')

        if not any(char.isupper() for char in passwd):
            raise ValidationError('Password should have at least one uppercase letter!')

        if not any(char.islower() for char in passwd):
            raise ValidationError('Password should have at least one lowercase letter!')

        if not any(char in spec_char for char in passwd):
            raise ValidationError('Password should have at least one special character!')


class UpdatePasswordForm(FlaskForm):
    # name = StringField('Full name', validators=[DataRequired()])
    # email = StringField('Email', validators=[DataRequired(), Email()])
    # area = SelectField('Area', coerce=int, validators=[DataRequired(), validate_select])
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'autocomplete': 'off'})
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')], render_kw={'autocomplete': 'off'})
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(UpdatePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_password(self, password):
        passwd = password.data
        spec_char = set(punctuation)

        if self.user.is_password_used(passwd):
            raise ValidationError('Invalid password, please create a different one!')

        if len(passwd) < 8:
            raise ValidationError('Password length should be at least 8 characters!')

        if len(passwd) > 50:
            raise ValidationError('Password length should be greater than 50 characters!')

        if not any(char.isdigit() for char in passwd):
            raise ValidationError('Password should have at least one number!')

        if not any(char.isupper() for char in passwd):
            raise ValidationError('Password should have at least one uppercase letter!')

        if not any(char.islower() for char in passwd):
            raise ValidationError('Password should have at least one lowercase letter!')

        if not any(char in spec_char for char in passwd):
            raise ValidationError('Password should have at least one special character!')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'autocomplete': 'off'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'autocomplete': 'off'})
    # shift = SelectField('Shift', coerce=int, validators=[InputRequired(), validate_select])
    captcha = StringField('Please enter the numbers and letters on the image below.',
                          validators=[DataRequired()], render_kw={'autocomplete': 'off'})
    captcha_token = HiddenField('captcha_token')
    captcha_img = HiddenField('captcha_img')
    # retry = HiddenField('retry', default=0)
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.captcha_image = self.captcha_img
        self.token = self.captcha_token.data
        if not self.captcha_token.data:
            captcha = gen_captcha()
            captcha_image = captcha[1]
            captcha_token = captcha[2]
            self.captcha_image = captcha_image
            self.token = captcha_token
            self.captcha_img.data = "data:image/png;base64," + b64encode(self.captcha_image.getvalue()).decode('ascii')


    def validate_captcha(self, captcha):
        captcha_string = jwt.decode(bytes(self.token, 'utf-8'), app.config['SECRET_KEY'], algorithms="HS256")['text']
        if captcha_string != captcha.data:
            raise ValidationError('Wrong input!')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={'autocomplete': 'off'})
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

    def __init__(self, user, *args, **kwargs):
        super(ResetPasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_password(self, password):
        passwd = password.data
        spec_char = set(punctuation)
        if self.user.is_password_used(passwd):
            raise ValidationError('Invalid password, please create a different one!')

        if len(passwd) < 8:
            raise ValidationError('Password length should be at least 8 characters!')

        if len(passwd) > 50:
            raise ValidationError('Password length should be greater than 50 characters!')

        if not any(char.isdigit() for char in passwd):
            raise ValidationError('Password should have at least one number!')

        if not any(char.isupper() for char in passwd):
            raise ValidationError('Password should have at least one uppercase letter!')

        if not any(char.islower() for char in passwd):
            raise ValidationError('Password should have at least one lowercase letter!')

        if not any(char in spec_char for char in passwd):
            raise ValidationError('Password should have at least one special character!')


user_designations = ['Nurse', 'Nursing Lead', 'Head Nurse', 'Educational Lead', 'Medical Technologist']


class EditProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # phone_no = StringField('Phone number(no spaces or dash)', validators=[DataRequired()])
    # designation = SelectField('Designation', validators=[DataRequired()], choices=user_designations)

    save = SubmitField('Save')

    def __init__(self, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter(func.lower(User.email) == self.email.data.lower().replace(' ', '')).first()
            if user is not None:
                raise ValidationError('Email is already registered!')


class AddNursingCourseForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    body = TextAreaField('Content')
    submit = SubmitField('Submit')