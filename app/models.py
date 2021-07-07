import jwt
from flask import redirect, url_for
from time import time as ttime

from datetime import datetime, timedelta, time

from app import app, db, login
from app.cme_models import cme_course_creators
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


@login.user_loader
def load_user(id):
    return User.query.get(id)


class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    subscription_json = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship('User', backref=db.backref('push_subscriptions'), lazy='joined')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), index=True, unique=True)
    phone_no = db.Column(db.String(64))
    employee_id = db.Column(db.String(64))
    # date_joined = db.Column(db.Date)
    password_hash = db.Column(db.String(128))
    designation_id = db.Column(db.Integer, db.ForeignKey('designation.id'))

    designation = db.relationship('Designation', backref=db.backref('users'), lazy='joined')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': ttime() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')#.decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_id_token(self, expires_in=1800):
        return jwt.encode(
            {'user_id': self.id, 'exp': ttime() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_id_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['user_id']
        except:
            return redirect(url_for('index'))
        return User.query.get(id)

    def is_password_expired(self):
        expired = False
        pw = UserPassword.query.filter_by(user_id=self.id, password_hash=self.password_hash).first()
        if pw:
            elapsed_time = datetime.now().date() - pw.date_registered
            if elapsed_time > timedelta(days=90):
                expired = True
        else:
            expired = True
        return expired

    def is_password_used(self, password):
        used = False
        for pwd in self.passwords_used[-10:]:
            if check_password_hash(pwd.password_hash, password):
                used = True
        return used

    def initials(self):
        initials = ''
        name_split = self.name.split()
        initials_ = [(x[0]) for n, x in enumerate(name_split) if n < 3]
        for x in initials_:
            initials += x
        return initials

    # def is_designation(self, designation_id):
    #     return self.designations.filter(
    #         user_designation.c.designation_id == designation_id).count() > 0

    def is_cme_course_creator(self):
        return self.cme_course_creator.filter(cme_course_creators.c.user_id == self.id).count() > 0

    # def current_shift(self):
    #     day_start = datetime.now().replace(hour=0, minute=0, second=1)
    #     day_end = datetime.now().replace(hour=23, minute=59, second=59)
    #     time = datetime.now().time()
    #     shift_ = Shift.query.filter(Shift.start <= time, Shift.end >= time).first()
    #     night = Shift.query.filter_by(name='Night').first()
    #     current_shift = UserShift.query.filter(UserShift.date.between(day_start, day_end)).filter_by(user_id=self.id).order_by(UserShift.date.desc()).first()
    #     shift = current_shift.shift if current_shift else shift_ if shift_ else night
    #     return shift

    def __repr__(self):
        return '<User {}>'.format(self.name)


class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128))
    ip_address = db.Column(db.String(128))
    date = db.Column(db.DateTime)
    success = db.Column(db.Boolean)
    error = db.Column(db.String(128))


class UserPassword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    password_hash = db.Column(db.String(128))
    date_registered = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('passwords_used'), lazy='joined')


# user_designation = db.Table('user_designation',
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('designation_id', db.Integer, db.ForeignKey('designation.id')),
# )


class Designation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))

    # users = db.relationship(
    #     'User', secondary='user_designation',
    #     backref=db.backref('designations', lazy='dynamic'), lazy='dynamic'
    # )


class NursingCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.String(5000))
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    submitted_by = db.relationship('User', foreign_keys='NursingCourse.submitted_by_id',
                                   backref=db.backref('nursing_course_submitter'), lazy='joined')
    approved_by = db.relationship('User', foreign_keys='NursingCourse.approved_by_id',
                                   backref=db.backref('nursing_course_approver'), lazy='joined')