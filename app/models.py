import jwt
import sys
from flask import redirect, url_for, flash
from time import time as ttime

from datetime import datetime, timedelta, time

from app import app, db, login
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy, BaseQuery


@login.user_loader
def load_user(id):
    return User.query.get(id)


# so that all deleted=True will not be included in the default query
class QueryWithSoftDelete(BaseQuery):
    _with_deleted = False

    def __new__(cls, *args, **kwargs):
        obj = super(QueryWithSoftDelete, cls).__new__(cls)
        obj._with_deleted = kwargs.pop('_with_deleted', False)
        if len(args) > 0:
            super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)
            return obj.filter_by(deleted=None) if not obj._with_deleted else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_deleted(self):
        return self.__class__(self._only_full_mapper_zero('get'),
                              session=db.session(), _with_deleted=True)

    def _get(self, *args, **kwargs):
        # this calls the original query.get function from the base class
        return super(QueryWithSoftDelete, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        # the query.get method does not like it if there is a filter clause
        # pre-loaded, so we need to implement it using a workaround
        obj = self.with_deleted()._get(*args, **kwargs)
        return obj if obj is None or self._with_deleted or not obj.deleted else None


class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    subscription_json = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('logs'), lazy='joined')
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='subquery'), lazy='joined')


#transferred here to avoid circular import error
cme_course_creators = db.Table('cme_course_creators',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('cme_course_id', db.Integer, db.ForeignKey('cme_course.id')),
)


user_logs = db.Table('user_logs',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), index=True, unique=True)
    phone_no = db.Column(db.String(64))
    employee_id = db.Column(db.String(64))
    date_joined = db.Column(db.Date)
    password_hash = db.Column(db.String(128))
    designation_id = db.Column(db.Integer, db.ForeignKey('designation.id'))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('user_logs'), lazy='joined')
    designation = db.relationship('Designation', backref=db.backref('users'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='user_logs',
        backref=db.backref('user_logs', lazy='dynamic'), lazy='dynamic'
    )

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
            return
        return User.query.get(id)

    def is_password_expired(self):
        expired = False
        pw = UserPassword.query.filter_by(user_id=self.id, password_hash=self.password_hash).first()
        if pw:
            elapsed_time = datetime.now() - pw.date_registered
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

    def is_active(self):
        return self.activations.filter(UserActivation.date_inactivated == None).count() > 0

    def is_cme_course_creator(self):
        course_creator = self.cme_course_creator.filter(cme_course_creators.c.user_id == self.id).count() > 0
        if self.is_cme_admin():
            course_creator = True
        return course_creator

    def is_cme_admin(self):
        return self.roles.filter(user_roles.c.role_id == 1).count() > 0 or current_user.id == 1

    def is_bb_admin(self):
        return self.roles.filter(user_roles.c.role_id == 2).count() > 0 or current_user.id == 1

    def is_admin(self):
        return self.roles.filter(user_roles.c.role_id == 1 or user_roles.c.role_id == 2).count() > 0 or current_user.id == 1

    def departments_list(self):
        departments_list = []
        for dept in self.departments:
            departments_list.append(dept)
        return departments_list

    query_class = QueryWithSoftDelete

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


class TwoFactorAuthentication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    two_fa_code = db.Column(db.String(6), index=True)
    token = db.Column(db.String(500))
    date_created = db.Column(db.DateTime)
    date_used = db.Column(db.DateTime)


activation_logs = db.Table('activation_logs',
    db.Column('user_activation_id', db.Integer, db.ForeignKey('user_activation.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class UserActivation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_activated = db.Column(db.DateTime)
    date_inactivated = db.Column(db.DateTime)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('activation_logs'), lazy='joined')
    user = db.relationship('User', backref=db.backref('activations', lazy='dynamic'))
    logs = db.relationship(
        'ActivityLog', secondary='activation_logs',
        backref=db.backref('activation_logs', lazy='dynamic'), lazy='dynamic'
    )


designation_logs = db.Table('designation_logs',
    db.Column('designation_id', db.Integer, db.ForeignKey('designation.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class Designation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('designation_logs'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='designation_logs',
        backref=db.backref('designation_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id,
             'user_id': current_user.id,
             'exp': ttime() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_id_token(token):
        try:
            decode = jwt.decode(token, app.config['SECRET_KEY'],
                                algorithms=['HS256'])
            id = decode['id']
            user_id = decode['user_id']
            if current_user.id != user_id:
                id = None
        except:
            return
        return Designation.query.get(id)


user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
)


role_logs = db.Table('role_logs',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('role_logs'), lazy='joined')

    users = db.relationship(
        'User', secondary='user_roles',
        backref=db.backref('roles', lazy='dynamic'), lazy='dynamic'
    )

    logs = db.relationship(
        'ActivityLog', secondary='role_logs',
        backref=db.backref('role_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id,
             'user_id': current_user.id,
             'exp': ttime() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_id_token(token):
        try:
            decode = jwt.decode(token, app.config['SECRET_KEY'],
                                algorithms=['HS256'])
            id = decode['id']
            user_id = decode['user_id']
            if current_user.id != user_id:
                id = None
        except:
            return
        return Role.query.get(id)

    def is_user_role(self, user):
        return self.users.filter(user_roles.c.user_id == user.id).count() > 0


user_departments = db.Table('user_departments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('department_id', db.Integer, db.ForeignKey('department.id')),
)


department_logs = db.Table('department_logs',
    db.Column('department_id', db.Integer, db.ForeignKey('department.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('role_logs'), lazy='joined')

    users = db.relationship(
        'User', secondary='user_departments',
        backref=db.backref('departments', lazy='dynamic'), lazy='dynamic'
    )

    logs = db.relationship(
        'ActivityLog', secondary='department_logs',
        backref=db.backref('department_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id,
             'user_id': current_user.id,
             'exp': ttime() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_id_token(token):
        try:
            decode = jwt.decode(token, app.config['SECRET_KEY'],
                                algorithms=['HS256'])
            id = decode['id']
            user_id = decode['user_id']
            if current_user.id != user_id:
                id = None
        except:
            return
        return Department.query.get(id)

    def is_user_department(self, user):
        return self.users.filter(user_departments.c.user_id == user.id).count() > 0


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log = db.Column(db.String(1000))
    date = db.Column(db.DateTime, default=datetime.now())

