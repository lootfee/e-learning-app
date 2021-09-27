import os
import jwt
from flask import redirect, url_for
from sqlalchemy import extract
from time import time as ttime

from app import app, db, login
from app.models import QueryWithSoftDelete, cme_course_creators, ActivityLog
from flask import jsonify, flash
from flask_login import UserMixin, current_user

from datetime import datetime, timedelta


cme_content_views = db.Table('cme_content_views',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('cme_course_content_id', db.Integer, db.ForeignKey('cme_course_content.id')),
)


cme_course_topic_logs = db.Table('cme_course_topic_logs',
    db.Column('cme_course_topic_id', db.Integer, db.ForeignKey('cme_course_topic.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourseTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(400))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('course_topic_logs'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_topic_logs',
        backref=db.backref('cme_course_topic_logs', lazy='dynamic'), lazy='dynamic'
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

        return CmeCourseTopic.query.get(id)

    def course_count(self, year, month):
        course_count = CmeCourse.query.filter(
            extract('year', CmeCourse.deadline) == year, extract('month', CmeCourse.deadline) == month).filter_by(
            topic_id=self.id
        ).count()
        return course_count


cme_course_logs = db.Table('cme_course_logs',
    db.Column('cme_course_id', db.Integer, db.ForeignKey('cme_course.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))
    cover_page = db.Column(db.String(256), index=True)
    cme_points = db.Column(db.Integer)
    cme_serial_no = db.Column(db.String(100))
    published = db.Column(db.Boolean)
    published_date = db.Column(db.DateTime)
    presentation_date = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    topic_id = db.Column(db.Integer, db.ForeignKey('cme_course_topic.id'))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('course_logs'), lazy='joined')
    topic = db.relationship('CmeCourseTopic', backref=db.backref('courses'), lazy='joined')
    creators = db.relationship(
        'User', secondary='cme_course_creators',
        backref=db.backref('cme_course_creator', lazy='dynamic'), lazy='dynamic'
    )
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_logs',
        backref=db.backref('cme_course_logs', lazy='dynamic'), lazy='dynamic'
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
        return CmeCourse.query.get(id)

    def is_creator(self, user):
        creator = self.creators.filter(cme_course_creators.c.user_id == user.id).count() > 0
        if current_user.is_cme_admin():
            creator = True
        return creator

    def open_pre_test(self, current_user):
        pre_test = CmeCoursePreTest.query.filter(CmeCoursePreTest.date_start.isnot(None)).filter_by(user_id=current_user.id, course_id=self.id, date_end=None).first()
        return pre_test

    def submitted_pre_test(self, current_user):
        pre_test = CmeCoursePreTest.query.filter(CmeCoursePreTest.date_start.isnot(None), CmeCoursePreTest.date_end.isnot(None)).filter_by(user_id=current_user.id, course_id=self.id).first()
        return pre_test

    def pre_test_start(self, current_user):
        start = False
        for pre_test in self.pre_tests:
            if pre_test.user_id == current_user.id and pre_test.date_start != None:
                start = True
        return start

    def pre_test_end(self, current_user):
        end = False
        for pre_test in self.pre_tests:
            if pre_test.user_id == current_user.id and pre_test.date_start != None and pre_test.date_end != None:
                end = True
        return end

    def open_post_test(self, current_user):
        post_test = CmeCoursePostTest.query.filter(CmeCoursePostTest.date_start.isnot(None)).filter_by(user_id=current_user.id, course_id=self.id, date_end=None).first()
        return post_test

    def submitted_post_test(self, current_user):
        post_test = CmeCoursePostTest.query.filter(
            CmeCoursePostTest.date_start.isnot(None), CmeCoursePostTest.date_end.isnot(None)).filter_by(
            user_id=current_user.id, course_id=self.id).order_by(CmeCoursePostTest.date_end.desc()).first()
        return post_test

    def post_test_start(self, current_user):
        start = False
        for post_test in self.post_tests:
            if post_test.user_id == current_user.id and post_test.date_start != None:
                start = True
        return start

    def post_test_end(self, current_user):
        end = False
        for post_test in self.post_tests:
            if post_test.user_id == current_user.id and post_test.date_start != None and post_test.date_end != None:
                end = True
        return end

    def is_completed(self, user):
        completed = 0
        for content in self.contents:
            if content.viewers.filter(cme_content_views.c.user_id == user.id).count() > 0:
                completed += 1

        return completed == len(self.contents)

    def release_certificate(self, user):
        # if self.cme_points != None: removed since doh approval nno longer required
        post_test = CmeCoursePostTest.query.filter(CmeCoursePostTest.date_end.isnot(None)).filter_by(course_id=self.id, user_id=user.id).order_by(
            CmeCoursePostTest.date_end.desc()).first()
        if post_test:
            percentage = (post_test.score / len(self.questions)) * 100
            return percentage >= 80

    def certificate_issue_date(self, user):
        n = -1
        last_pt_passed = self.user_post_tests(user)[n] if self.user_post_tests(user)[
            n].passed() else self.user_post_tests(user)[n - 1]
        issue_date = last_pt_passed.date_end
        return issue_date

    def user_post_tests(self, user):
        post_tests = []
        for post in self.post_tests:
            if post.user_id == user.id:
                post_tests.append(post)
        return post_tests

    def has_been_reviewed(self, user):
        reviewed = False
        users_rev = []
        for rev in self.user_reviews:
            users_rev.append(rev.user_id)
        if user.id in users_rev:
            reviewed = True
        return reviewed


    # def ongoing(self):
    #     return datetime.now() > self.deadline
    #
    # def ended(self):
    #     return datetime.now() <= self.deadline


cme_course_content_logs = db.Table('cme_course_content_logs',
    db.Column('cme_course_content_id', db.Integer, db.ForeignKey('cme_course_content.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourseContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))
    index = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('course_content_logs'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('contents'), lazy='joined')

    viewers = db.relationship(
        'User', secondary='cme_content_views',
        backref=db.backref('cme_content_views', lazy='dynamic'), lazy='dynamic'
    )
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_content_logs',
        backref=db.backref('cme_course_content_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCourseContent.query.get(id)

    def is_completed(self, user):
        return self.viewers.filter(cme_content_views.c.user_id == user.id).count() > 0


cme_content_slide_logs = db.Table('cme_content_slide_logs',
    db.Column('cme_content_slides_id', db.Integer, db.ForeignKey('cme_content_slides.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)



class CmeContentSlides(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(256), index=True)
    sound_file = db.Column(db.String(256), index=True)
    slide_text = db.Column(db.String(4000))
    index = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    course_content_id = db.Column(db.Integer, db.ForeignKey('cme_course_content.id'))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('content_slide_logs'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('slides'), lazy='joined')
    course_content = db.relationship('CmeCourseContent', backref=db.backref('slides'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_content_slide_logs',
        backref=db.backref('cme_content_slide_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeContentSlides.query.get(id)


cme_content_video_logs = db.Table('cme_content_video_logs',
    db.Column('cme_content_video_id', db.Integer, db.ForeignKey('cme_content_video.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeContentVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_file = db.Column(db.String(256), index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    course_content_id = db.Column(db.Integer, db.ForeignKey('cme_course_content.id'))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('content_video_logs'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('video'), lazy='joined')
    course_content = db.relationship('CmeCourseContent', backref=db.backref('video', uselist=False), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_content_video_logs',
        backref=db.backref('cme_content_video_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeContentVideo.query.get(id)


cme_course_question_logs = db.Table('cme_course_question_logs',
    db.Column('cme_course_question_id', db.Integer, db.ForeignKey('cme_course_question.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourseQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000))
    answer_explanation = db.Column(db.String(1000))
    image_file = db.Column(db.String(256), index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    deleted = db.Column(db.Boolean)

    # log = db.relationship('ActivityLog', backref=db.backref('course_question_logs'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('questions'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_question_logs',
        backref=db.backref('cme_course_question_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCourseQuestion.query.get(id)

    def answer(self):
        for a in self.choices:
            if a.answer == True:
                return a


cme_course_question_choices_logs = db.Table('cme_course_question_choices_logs',
    db.Column('cme_course_question_choices_id', db.Integer, db.ForeignKey('cme_course_question_choices.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourseQuestionChoices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400))
    answer = db.Column(db.Boolean)
    question_id = db.Column(db.Integer, db.ForeignKey('cme_course_question.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    deleted = db.Column(db.Boolean)
    # log_id = db.Column(db.Integer, db.ForeignKey('activity_log.id'))
    #
    # log = db.relationship('ActivityLog', backref=db.backref('course_question_choices_logs'), lazy='joined')
    question = db.relationship('CmeCourseQuestion', backref=db.backref('choices'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('choices'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_question_choices_logs',
        backref=db.backref('cme_course_question_choices_logs', lazy='dynamic'), lazy='dynamic'
    )

    query_class = QueryWithSoftDelete

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCourseQuestionChoices.query.get(id)


cme_course_pre_test_logs = db.Table('cme_course_pre_test_logs',
    db.Column('cme_course_pre_test_id', db.Integer, db.ForeignKey('cme_course_pre_test.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCoursePreTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_start = db.Column(db.DateTime)
    date_end = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    course = db.relationship('CmeCourse', backref=db.backref('pre_tests'), lazy='joined')
    user = db.relationship('User', backref=db.backref('pre_tests'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_pre_test_logs',
        backref=db.backref('cme_course_pre_test_logs', lazy='dynamic'), lazy='dynamic'
    )

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCoursePreTest.query.get(id)

    def has_response(self, question):
        response = CmeCoursePreTestResponse.query.filter_by(
            pretest_id=self.id, user_id=self.user_id, course_id=self.course_id, question_id=question.id).first()
        return response

    def post_test_score(self):
        post_test = CmeCoursePostTest.query.filter_by(course_id=self.course_id, user_id=self.user_id).first()
        return post_test.score

    def percent_score(self):
        percentage = int(round((self.score / len(self.course.questions)) * 100))
        return percentage


cme_course_pre_test_response_logs = db.Table('cme_course_pre_test_response_logs',
    db.Column('cme_course_pre_test_response_id', db.Integer, db.ForeignKey('cme_course_pre_test_response.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCoursePreTestResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pretest_id = db.Column(db.Integer, db.ForeignKey('cme_course_pre_test.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('cme_course_question.id'))
    selected_choice_id = db.Column(db.Integer, db.ForeignKey('cme_course_question_choices.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    pretest = db.relationship('CmeCoursePreTest', backref=db.backref('pre_test_response'), lazy='joined')
    question = db.relationship('CmeCourseQuestion', backref=db.backref('pre_test_response'), lazy='joined')
    selected_choice = db.relationship('CmeCourseQuestionChoices', backref=db.backref('pre_test_response'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('pre_test_response'), lazy='joined')
    user = db.relationship('User', backref=db.backref('pre_test_response'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_pre_test_response_logs',
        backref=db.backref('cme_course_pre_test_response_logs', lazy='dynamic'), lazy='dynamic'
    )

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCoursePreTestResponse.query.get(id)


cme_course_post_test_logs = db.Table('cme_course_post_test_logs',
    db.Column('cme_course_post_test_id', db.Integer, db.ForeignKey('cme_course_post_test.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCoursePostTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_start = db.Column(db.DateTime)
    date_end = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    course = db.relationship('CmeCourse', backref=db.backref('post_tests'), lazy='joined')
    user = db.relationship('User', backref=db.backref('post_tests'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_post_test_logs',
        backref=db.backref('cme_course_post_test_logs', lazy='dynamic'), lazy='dynamic'
    )

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCoursePostTest.query.get(id)

    def has_response(self, question):
        response = CmeCoursePostTestResponse.query.filter_by(
            posttest_id=self.id, user_id=self.user_id, course_id=self.course_id, question_id=question.id).first()
        return response

    def passed(self):
        if self.date_end:
            percentage = (self.score / len(self.course.questions)) * 100
            return percentage >= 80

    def pre_test_score(self):
        pre_test = CmeCoursePreTest.query.filter_by(course_id=self.course_id, user_id=self.user_id).first()
        return pre_test.score

    def percent_score(self):
        percentage = int(round((self.score / len(self.course.questions)) * 100))
        return percentage


cme_course_post_test_response_logs = db.Table('cme_course_post_test_response_logs',
    db.Column('cme_course_post_test_response_id', db.Integer, db.ForeignKey('cme_course_post_test_response.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCoursePostTestResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posttest_id = db.Column(db.Integer, db.ForeignKey('cme_course_post_test.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('cme_course_question.id'))
    selected_choice_id = db.Column(db.Integer, db.ForeignKey('cme_course_question_choices.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    posttest = db.relationship('CmeCoursePostTest', backref=db.backref('post_test_response'), lazy='joined')
    question = db.relationship('CmeCourseQuestion', backref=db.backref('post_test_response'), lazy='joined')
    selected_choice = db.relationship('CmeCourseQuestionChoices', backref=db.backref('post_test_response'), lazy='joined')
    course = db.relationship('CmeCourse', backref=db.backref('post_test_response'), lazy='joined')
    user = db.relationship('User', backref=db.backref('post_test_response'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_post_test_response_logs',
        backref=db.backref('cme_course_post_test_response_logs', lazy='dynamic'), lazy='dynamic'
    )

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCoursePostTestResponse.query.get(id)


cme_course_user_question_logs = db.Table('cme_course_user_question_logs',
    db.Column('cme_course_user_question_id', db.Integer, db.ForeignKey('cme_course_user_question.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourseUserQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(1000))
    answer = db.Column(db.String(5000))
    date_posted = db.Column(db.DateTime)
    date_answered = db.Column(db.DateTime)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    questioned_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answered_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    course = db.relationship('CmeCourse', backref=db.backref('user_questions'), lazy='joined')
    questioned_by = db.relationship('User', foreign_keys='CmeCourseUserQuestion.questioned_by_id', backref=db.backref('course_user_questions'), lazy='joined')
    answered_by = db.relationship('User', foreign_keys='CmeCourseUserQuestion.answered_by_id', backref=db.backref('course_user_answers'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_user_question_logs',
        backref=db.backref('cme_course_user_question_logs', lazy='dynamic'), lazy='dynamic'
    )

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCourseUserQuestion.query.get(id)


cme_course_review_logs = db.Table('cme_course_review_logs',
    db.Column('cme_course_review_id', db.Integer, db.ForeignKey('cme_course_review.id')),
    db.Column('activity_log_id', db.Integer, db.ForeignKey('activity_log.id')),
)


class CmeCourseReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('cme_course.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_submitted = db.Column(db.DateTime)
    q1 = db.Column(db.Integer())
    q2 = db.Column(db.Integer())
    q3 = db.Column(db.Integer())
    q4 = db.Column(db.Integer())
    q5 = db.Column(db.Integer())
    q6 = db.Column(db.Integer())
    q7 = db.Column(db.Integer())
    q8 = db.Column(db.Integer())
    q9 = db.Column(db.Integer())
    q10 = db.Column(db.Integer())
    q11 = db.Column(db.Integer())
    q12 = db.Column(db.Integer())
    q13 = db.Column(db.Integer())
    q14 = db.Column(db.Integer())
    q15 = db.Column(db.Integer())
    q16 = db.Column(db.Integer())
    q17 = db.Column(db.Integer())
    q18 = db.Column(db.Integer())
    q19 = db.Column(db.Integer())
    q20 = db.Column(db.Integer())
    q21 = db.Column(db.String(5000))
    q22 = db.Column(db.String(5000))

    course = db.relationship('CmeCourse', backref=db.backref('user_reviews'), lazy='joined')
    user = db.relationship('User', backref=db.backref('course_reviews'), lazy='joined')
    logs = db.relationship(
        'ActivityLog', secondary='cme_course_review_logs',
        backref=db.backref('cme_course_review_logs', lazy='dynamic'), lazy='dynamic'
    )

    def get_id_token(self, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'user_id': current_user.id, 'exp': ttime() + expires_in},
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
        return CmeCourseReview.query.get(id)