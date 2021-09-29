import os
import jwt
from flask import redirect, url_for
from sqlalchemy import extract
from time import time as ttime

from app import app, db, login
from app.models import QueryWithSoftDelete, ActivityLog, Designation, Department
from flask import jsonify
from flask_login import UserMixin, current_user

from datetime import datetime, timedelta


bulletin_topic_logs = db.Table('bulletin_topic_logs',
    db.Column('bulletin_topic_id', db.Integer, db.ForeignKey('bulletin_topic.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class BulletinTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(400))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('bulletin_topic_logs'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='bulletin_topic_logs',
        backref=db.backref('bulletin_topic_logs', lazy='dynamic'), lazy='dynamic'
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
        return BulletinTopic.query.get(id)


bulletin_logs = db.Table('bulletin_logs',
    db.Column('bulletin_id', db.Integer, db.ForeignKey('bulletin.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)

bulletin_departments = db.Table('bulletin_departments',
    db.Column('bulletin_id', db.Integer, db.ForeignKey('bulletin.id')),
    db.Column('department_id', db.Integer, db.ForeignKey('department.id')),
)

bulletin_designations = db.Table('bulletin_designations',
    db.Column('bulletin_id', db.Integer, db.ForeignKey('bulletin.id')),
    db.Column('designation_id', db.Integer, db.ForeignKey('designation.id')),
)


class Bulletin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))
    content = db.Column(db.String(40000))
    topic_id = db.Column(db.Integer, db.ForeignKey('bulletin_topic.id'))
    cover_pic = db.Column(db.String(400))
    important = db.Column(db.Boolean)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_date = db.Column(db.DateTime)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approve_date = db.Column(db.DateTime)
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('bulletin_logs'), lazy='joined')
    topic = db.relationship('BulletinTopic', backref=db.backref('bulletins'), lazy='joined')
    submitted_by = db.relationship('User', foreign_keys='Bulletin.submitted_by_id', backref=db.backref('bulletins_submitted'), lazy='joined')
    approved_by = db.relationship('User', foreign_keys='Bulletin.approved_by_id', backref=db.backref('bulletins_approved'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='bulletin_logs',
        backref=db.backref('bulletin_logs', lazy='dynamic'), lazy='dynamic'
    )
    departments = db.relationship(
        'Department', secondary='bulletin_departments',
        backref=db.backref('bulletin_departments', lazy='dynamic'), lazy='dynamic'
    )
    designations = db.relationship(
        'Designation', secondary='bulletin_designations',
        backref=db.backref('bulletin_designations', lazy='dynamic'), lazy='dynamic'
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
        return Bulletin.query.get(id)

    def departments_list(self):
        departments_list = []
        for dept in self.departments:
            departments_list.append(dept)
        return departments_list

    def designations_list(self):
        designations_list = []
        for desig in self.designations:
            designations_list.append(desig)
        return designations_list

    def is_target_viewer(self, user):
        is_target_viewer = False
        is_desig = self.designations.filter(bulletin_designations.c.designation_id == user.designation_id).count() > 0
        self_dept = self.departments.all()
        user_dept = user.departments.all()
        is_dept = any(x in self_dept for x in user_dept)
        if is_desig and is_dept:
            is_target_viewer = True
        return is_target_viewer

    def view_count(self):
        return len(self.viewers)

    def viewer_list(self):
        viewer_list = []
        for viewer in self.viewers:
            viewer_list.append(viewer.viewer)
        return viewer_list

    def comment_count(self):
        return len(self.comments)

    def coverpage(self):
        if self.attachments:
            if self.attachments[0].filetype in ['jpg', 'jpeg', 'png', 'gif']:
                coverpage = self.attachments[0].filepath
                return coverpage


bulletin_attachment_logs = db.Table('bulletin_attachment_logs',
    db.Column('bulletin_attachment_id', db.Integer, db.ForeignKey('bulletin_attachment.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class BulletinAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin.id'))
    filepath = db.Column(db.String(400))
    filename = db.Column(db.String(400))
    filetype = db.Column(db.String(10))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('bulletin_attachment_logs'), lazy='joined')
    bulletin = db.relationship('Bulletin', backref=db.backref('attachments'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='bulletin_attachment_logs',
        backref=db.backref('bulletin_attachment_logs', lazy='dynamic'), lazy='dynamic'
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
        return BulletinAttachment.query.get(id)


bulletin_comment_logs = db.Table('bulletin_comment_logs',
    db.Column('bulletin_comment_id', db.Integer, db.ForeignKey('bulletin_comment.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class BulletinComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin.id'))
    comment = db.Column(db.String(1000))
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_date = db.Column(db.DateTime)
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('bulletin_comment_logs'), lazy='joined')
    bulletin = db.relationship('Bulletin', backref=db.backref('comments'), lazy='joined')
    submitted_by = db.relationship('User', backref=db.backref('comments'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='bulletin_comment_logs',
        backref=db.backref('bulletin_comment_logs', lazy='dynamic'), lazy='dynamic'
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
        return BulletinComment.query.get(id)


class BulletinViewer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bulletin_id = db.Column(db.Integer, db.ForeignKey('bulletin.id'))
    viewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    view_date = db.Column(db.DateTime)

    bulletin = db.relationship('Bulletin', backref=db.backref('viewers'), lazy='joined')
    viewer = db.relationship('User', backref=db.backref('bulletin_views'), lazy='joined')

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
        return BulletinViewer.query.get(id)