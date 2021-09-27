from flask import render_template
from flask_mail import Message
from app import app, mail
from app.models import User, Role

from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipients, html_body, cc):
    msg = Message(subject, recipients=recipients, cc=cc)
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()
    #send_async_email(app, msg)
    '''try:
        mail.send(msg)
    except TimeoutError:
        pass'''


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    print(token)
    send_email('Reset Your Password',
               #sender=app.config['ADMINS'][0],
               recipients=[user.email], cc=None,
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_new_user_password_email(user):
    token = user.get_reset_password_token()
    print(token)
    send_email('Create Your Password',
               #sender=app.config['ADMINS'][0],
               recipients=[user.email], cc=None,
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))


def send_registration_confirmation_email(email, name, token, two_factor_auth_code):
    send_email('Biogenix app email confirmation.',
               #sender=app.config['ADMINS'][0],
               recipients=[email], cc=None,
               html_body=render_template('email/registration_confirmation.html', name=name, token=token, two_factor_auth_code=two_factor_auth_code))


def send_password_update_confirmation_email(email, name, token, two_factor_auth_code):
    send_email('Biogenix app email confirmation.',
               #sender=app.config['ADMINS'][0],
               recipients=[email], cc=None,
               html_body=render_template('email/password_update_confirmation.html', name=name, token=token,
                                         two_factor_auth_code=two_factor_auth_code))


def email_user(user_id, subject, body):
    user = User.query.filter_by(id=user_id).first()
    send_email(subject, cc=None,
               recipients=[user.email],
               html_body=render_template('email/notify.html', body=body, user=user.name))


def email_admins(subject, body):
    users = Role.query.filter(Role.id <= 2).all()
    cc = []
    for user in users[1:]:
        cc.append(user.email)
    send_email(subject,
               recipients=[users[0].email], cc=cc,
               html_body=render_template('email/notify.html', body=body, user=user.name))


def email_course_admins(subject, body):
    users = Role.query.filter(Role.id == 1).all()
    cc = []
    for user in users[1:]:
        cc.append(user.email)
    send_email(subject,
               recipients=[users[0].email], cc=cc,
               html_body=render_template('email/notify.html', body=body, user=user.name))


def email_bb_admins(subject, body):
    users = Role.query.filter(Role.id == 2).all()
    cc = []
    for user in users[1:]:
        cc.append(user.email)
    send_email(subject,
               recipients=[users[0].email], cc=cc,
               html_body=render_template('email/notify.html', body=body, user=user.name))


def email_course_creators(users, subject, body):
    # users = Role.query.filter(Role.id == 1).all()
    cc = []
    for user in users[1:]:
        cc.append(user.email)
    send_email(subject,
               recipients=[users[0].email], cc=cc,
               html_body=render_template('email/notify.html', body=body, user=user.name))