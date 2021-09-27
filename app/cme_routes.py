import os
import statistics
import imghdr
import random
import io
import re
import calendar
# import pdfkit


from app import app, db
from flask import render_template, flash, redirect, url_for, request, abort, send_from_directory, jsonify, send_file
from flask_login import current_user, login_user, logout_user, login_required
# from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
# from sqlalchemy import func, extract
from gtts import gTTS

from app.models import User
from app.cme_forms import *
from app.cme_models import *
from app.email import email_user, email_course_creators
from app.pdf_builder import create_cme_certificate_pdf
from app.web_push_handler import trigger_push_notifications_for_user_designation, trigger_push_notifications_for_user

from datetime import date, datetime, timedelta, time
# from dateutil import parser
# import calendar


def allowed_cme_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def allowed_cme_video(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mp4', 'mov', 'wmv', 'avi', 'flv'}


@app.route('/learning_hub', methods=['GET', 'POST'])
@login_required
def continuing_medical_education():
    open_courses = CmeCourse.query.filter(CmeCourse.deadline > datetime.now()).filter_by(published=True).order_by(
        CmeCourse.presentation_date.desc()).all()
    ended_courses = CmeCourse.query.filter(CmeCourse.deadline < datetime.now()).filter_by(published=True).order_by(
        CmeCourse.presentation_date.desc()).all()
    return render_template('cme/cme_main.html', open_courses=open_courses, ended_courses=ended_courses)


@app.route('/learning_hub/course_content/<token>/<int:content_index>', methods=['GET', 'POST'])
@login_required
def cme_course_content(token, content_index):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))

    # print(course.is_completed(current_user))
    if course.published == False:
        return redirect(url_for('continuing_medical_education'))
    if not course.submitted_post_test(current_user) and datetime.now() > course.deadline:
        return redirect(url_for('continuing_medical_education'))

    content = None
    if content_index != 0:
        if course.pre_test_end(current_user) == False:
            flash('Please take pre-test before proceeding', 'alert-warning')
            return redirect(url_for('cme_course_content', token=course.get_id_token(), content_index=0))
        content = CmeCourseContent.query.filter_by(course_id=course.id, index=content_index).first()
        previous_content = CmeCourseContent.query.filter_by(course_id=course.id, index=content_index - 1).first()
        if previous_content:
            if previous_content.is_completed(current_user) == False:
                flash('Please complete current lesson before proceeding to the next one', 'alert-warning')
                return redirect(url_for('cme_course_content', token=course.get_id_token(), content_index=previous_content.index))
    # emp_id_form = EmployeeIdForm()
    # if emp_id_form.validate_on_submit():
    #     current_user.employee_id = emp_id_form.employee_id.data.upper()
    #     db.session.commit()
    #     return redirect(url_for('cme_course_content', token=course.get_id_token(), content_index=content_index))

    course_question_form = CourseQuestionForm()
    if course_question_form.submit.data:
        if course_question_form.validate_on_submit():
            question = CmeCourseUserQuestion(course_id=course.id,
                                         question=course_question_form.question.data,
                                         questioned_by_id=current_user.id,
                                         date_posted=datetime.now())
            db.session.add(question)
            db.session.commit()
            log = ActivityLog(
                log=f'question-{question.id}-{question.question} submited by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            question.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()

            flash('Your question has been submitted. You will be notified once your question is answered', 'alert-info')
            subject = f'Question submitted for {course.title}.'
            body = f'{question.questioned_by.name} submitted a question: \n \n {question.question}'
            email_course_creators(course.creators, subject=subject, body=body)
            push_json = {"title": f"Course Question Submitted",
                         "body": f'{question.questioned_by.name} submitted a question for {course.title} course.',
                         }
            trigger_push_notifications_for_user_designation(push_json, course.creators)
            return redirect(url_for('cme_course_content', token=course.get_id_token(), content_index=content_index))
    return render_template('cme/cme_course_content.html', course=course, content=content,
                           content_index=content_index, course_question_form=course_question_form)


@app.route('/learning_hub/complete_lesson/<token>', methods=['GET', 'POST'])
@login_required
def cme_complete_lesson(token):
    content = CmeCourseContent.verify_id_token(token)
    if not content:
        return redirect(url_for('continuing_medical_education'))
    if current_user not in content.viewers:
        content.viewers.append(current_user)
        db.session.commit()
        log = ActivityLog(
            log=f'content-{content.id} completed by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        content.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
    return redirect(url_for('cme_course_content', token=content.course.get_id_token(), content_index=content.index + 1))


@app.route('/learning_hub/take_pre_test/<course_token>/<question_token>', methods=['GET'])
@login_required
def cme_take_pre_test(course_token, question_token):
    course = CmeCourse.verify_id_token(course_token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if course.pre_test_end(current_user):
        flash('You have already taken pre-test for this course.', 'alert-warning')
        return redirect(url_for('cme_course_content', token=course.get_id_token(), content_index=0))
    elif course.pre_test_start(current_user):
        pre_test = course.open_pre_test(current_user)
        question = CmeCourseQuestion.verify_id_token(question_token)

        return render_template('cme/cme_pre_test.html', course=course, pre_test=pre_test, question=question)
    else:
        pre_test = CmeCoursePreTest(date_start=datetime.now(),
                                    course_id=course.id,
                                    user_id=current_user.id)
        db.session.add(pre_test)
        db.session.commit()
        log = ActivityLog(
            log=f'Course {course.id}-{course.title} pre-test started by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        pre_test.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return render_template('cme/cme_pre_test.html', course=course, question=None)


@app.route('/learning_hub/submit_pretest_response/<course_token>/<question_token>)', methods=['POST'])
@login_required
def submit_pretest_response(course_token, question_token):
    course = CmeCourse.verify_id_token(course_token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    question = CmeCourseQuestion.verify_id_token(question_token)
    if not question:
        return redirect(url_for('continuing_medical_education'))
    pre_test = course.open_pre_test(current_user)
    choice_id = request.form.get('question_radios')
    q_index = course.questions.index(question)
    try:
        next_question = course.questions[q_index + 1]
    except IndexError:
        next_question = course.questions[q_index]
    if choice_id:
        response_q = CmeCoursePreTestResponse.query.filter_by(pretest_id=pre_test.id,
                                                              question_id=question.id,
                                                              course_id=course.id,
                                                              user_id=current_user.id).first()
        if response_q:
            response_q.selected_choice_id = choice_id
            db.session.commit()
            log = ActivityLog(
                log=f'pre_test_response-{response_q.id} choice-{response_q.selected_choice_id} edited by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            response_q.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()
            return redirect(url_for('cme_take_pre_test', course_token=course.get_id_token(), question_token=next_question.get_id_token()))
        else:
            answer = CmeCoursePreTestResponse(pretest_id=pre_test.id,
                                              question_id=question.id,
                                              selected_choice_id=choice_id,
                                              course_id=course.id,
                                              user_id=current_user.id)
            db.session.add(answer)
            db.session.commit()
            log = ActivityLog(
                log=f'pre_test_response-{answer.id} choice-{answer.selected_choice_id} submitted by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            answer.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()
            return redirect(url_for('cme_take_pre_test', course_token=course.get_id_token(), question_token=next_question.get_id_token()))
    else:
        flash('Response not saved, no answer selected!', 'alert-warning')
        return redirect(url_for('cme_take_pre_test', course_token=course.get_id_token(), question_token=next_question.get_id_token()))


@app.route('/learning_hub/submit_pretest/<token>', methods=['GET', 'POST'])
@login_required
def submit_pretest(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if course.pre_test_start(current_user):
        pre_test = course.open_pre_test(current_user)
        score = 0
        answered_questions = 0
        for q in course.questions:
            if pre_test.has_response(q):
                answered_questions += 1
                if pre_test.has_response(q).selected_choice_id == q.answer().id:
                    score += 1

        if answered_questions != len(course.questions):
            flash('There are still questions that have not been answered!', 'alert-warning')
            return redirect(url_for('cme_take_pre_test', course_token=course.get_id_token(), question_token=course.questions[0].get_id_token()))

        pre_test.score = score
        pre_test.date_end = datetime.now()
        db.session.commit()
        log = ActivityLog(
            log=f'Course {course.id}-{course.title} pre-test submitted by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        course.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return redirect(url_for('pre_test_summary', token=course.get_id_token()))


@app.route('/learning_hub/pre_test_summary/<token>', methods=['GET', 'POST'])
@login_required
def pre_test_summary(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if course.pre_test_end(current_user):
        pre_test = course.submitted_pre_test(current_user)
        return render_template('cme/cme_pre_test_summary.html', pre_test=pre_test)
    else:
        flash('Pre-test has not been submitted!', 'alert-warning')
        return redirect(url_for('cme_take_pre_test', course_token=course.get_id_token(), question_token=course.questions[0].get_id_token()))


@app.route('/learning_hub/take_post_test/<course_token>/<question_token>', methods=['GET'])
@login_required
def cme_take_post_test(course_token, question_token):
    course = CmeCourse.verify_id_token(course_token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    # if course.post_test_end(current_user):
    #     flash('You have already taken post-test for this course.', 'alert-warning')
    #     return redirect(url_for('cme_course_content', course_id=course.id, course_title=course.title, content_index=0))
    if course.open_post_test(current_user):# course.post_test_start(current_user) and not course.post_test_end(current_user):
        post_test = course.open_post_test(current_user)
        question = CmeCourseQuestion.verify_id_token(question_token)
        return render_template('cme/cme_post_test.html', course=course, post_test=post_test, question=question)
    else:
        post_test = CmeCoursePostTest(date_start=datetime.now(),
                                    course_id=course.id,
                                    user_id=current_user.id)
        db.session.add(post_test)
        db.session.commit()
        log = ActivityLog(
            log=f'Course {course.id}-{course.title} post-test started by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        course.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return render_template('cme/cme_post_test.html', course=course, question=None)


@app.route('/learning_hub/submit_post_test_response/<course_token>/<question_token>', methods=['POST'])
@login_required
def submit_post_test_response(course_token, question_token):
    course = CmeCourse.verify_id_token(course_token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    question = CmeCourseQuestion.verify_id_token(question_token)
    if not question:
        return redirect(url_for('continuing_medical_education'))
    post_test = course.open_post_test(current_user)
    choice_id = request.form.get('question_radios')

    q_index = course.questions.index(question)
    try:
        next_question = course.questions[q_index + 1]
    except IndexError:
        next_question = course.questions[q_index]
    if choice_id:
        response_q = CmeCoursePostTestResponse.query.filter_by(posttest_id=post_test.id,
                                                              question_id=question.id,
                                                              course_id=course.id,
                                                              user_id=current_user.id).first()
        if response_q:
            response_q.selected_choice_id = choice_id
            db.session.commit()
            log = ActivityLog(
                log=f'post-test-response {response_q.id} choice-{response_q.selected_choice_id} edited by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            response_q.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()
            return redirect(url_for('cme_take_post_test', token=course.get_id_token(), question_token=next_question.get_id_token()))
        else:
            answer = CmeCoursePostTestResponse(posttest_id=post_test.id,
                                              question_id=question.id,
                                              selected_choice_id=choice_id,
                                              course_id=course.id,
                                              user_id=current_user.id)
            db.session.add(answer)
            db.session.commit()
            log = ActivityLog(
                log=f'post-test-response {answer.id} choice-{answer.selected_choice_id} submitted by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            answer.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()
            return redirect(url_for('cme_take_post_test', course_token=course.get_id_token(), question_token=next_question.get_id_token()))
    else:
        flash('Response not saved, no answer selected!', 'alert-warning')
        return redirect(url_for('cme_take_post_test', course_token=course.get_id_token(), question_token=next_question.get_id_token()))


@app.route('/learning_hub/submit_post_test/<token>', methods=['GET', 'POST'])
@login_required
def submit_post_test(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if course.open_post_test(current_user):
        post_test = course.open_post_test(current_user)
        score = 0
        answered_questions = 0
        for q in course.questions:
            if post_test.has_response(q):
                answered_questions += 1
                if post_test.has_response(q).selected_choice_id == q.answer().id:
                    score += 1

        if answered_questions != len(course.questions):
            flash('There are still questions that have not been answered!', 'alert-warning')
            return redirect(url_for('cme_take_post_test', course_token=course.get_id_token(), question_token=course.questions[0].get_id_token()))

        post_test.score = score
        post_test.date_end = datetime.now()
        db.session.commit()
        log = ActivityLog(
            log=f'Course {course.id}-{course.title} post-test submitted by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        course.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return redirect(url_for('post_test_summary', token=course.get_id_token()))


@app.route('/learning_hub/post_test_summary/<token>', methods=['GET', 'POST'])
@login_required
def post_test_summary(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if course.post_test_end(current_user):
        post_test = course.submitted_post_test(current_user)
        return render_template('cme/cme_post_test_summary.html', post_test=post_test)
    else:
        flash('Post-test has not been submitted!', 'alert-warning')
        return redirect(url_for('cme_take_post_test', course_token=course.get_id_token(), question_token=course.questions[0].get_id_token()))


@app.route('/learning_hub/course_user_questions/<token>', methods=['GET', 'POST'])
@login_required
def cme_course_user_questions(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('index'))
    form = CourseQuestionAnswerForm()
    if form.validate_on_submit():
        question = CmeCourseUserQuestion.query.get(form.question_id.data)
        question.answer = form.answer.data
        question.answered_by_id = current_user.id
        question.date_answered = datetime.now()
        print(question.answer, question.answered_by_id, question.date_answered)
        db.session.commit()
        log = ActivityLog(
            log=f'Course {course.id}-{course.title} question-{question} answered by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        question.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": f"Course Question Answered",
                     "body": f'Your question for the course {course.title} has been answered by {question.answered_by.name}.',
                     }
        trigger_push_notifications_for_user(push_json, question.questioned_by)
        flash('Question answered', 'alert-info')
        return redirect(url_for('cme_course_user_questions', token=course.get_id_token()))
    return render_template('cme/cme_course_user_questions.html', course=course, form=form)


@app.route('/learning_hub/get_user_questions/<int:course_id>', methods=['GET'])
@login_required
def get_cme_user_questions(course_id):
    course = CmeCourse.query.get(course_id)
    questions = []
    for question in course.user_questions:
        if question.answer:
            questions.append({'question_id': question.id,
                              'question': question.question,
                              'posted_by': question.questioned_by.name,
                              'date_posted': question.date_posted.strftime('%b %d, %Y'),
                              'answer': question.answer,
                              'answered_by': question.answered_by.name,
                              'date_answered': question.date_answered.strftime('%b %d, %Y'),
                              })
    return jsonify(questions)


@app.route('/learning_hub/my_certificates', methods=['GET', 'POST'])
@login_required
def cme_my_certificates():
    courses = CmeCourse.query.all()
    certificates = []
    for c in courses:
        if c.release_certificate(current_user):
            certificates.append(c)
            # create_cme_certificate(current_user, c)
    return render_template('cme/cme_user_certificates.html', certificates=certificates)


@app.route('/learning_hub/course_certificate/<token>', methods=['GET', 'POST'])
@login_required
def cme_course_certificate(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if course.release_certificate(current_user):
        return render_template('cme/cme_certificate.html', course=course)


@app.route('/learning_hub/review_course/<token>', methods=['GET', 'POST'])
@login_required
def cme_review_course(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        return redirect(url_for('continuing_medical_education'))
    if not course.release_certificate(current_user) or course.has_been_reviewed(current_user):
        return redirect(url_for('continuing_medical_education'))

    form = CourseReviewForm()
    if form.validate_on_submit():
        review = CmeCourseReview(course_id=course.id,
                                 user_id=current_user.id,
                                 date_submitted=datetime.now(),
                                 q1=form.q1.data,
                                 q2=form.q2.data,
                                 q3=form.q3.data,
                                 q4=form.q4.data,
                                 q5=form.q5.data,
                                 q6=form.q6.data,
                                 q7=form.q7.data,
                                 q8=form.q8.data,
                                 q9=form.q9.data,
                                 q10=form.q10.data,
                                 q11=form.q11.data,
                                 q12=form.q12.data,
                                 q13=form.q13.data,
                                 q14=form.q14.data,
                                 q15=form.q15.data,
                                 q16=form.q16.data,
                                 q17=form.q17.data,
                                 q18=form.q18.data,
                                 q19=form.q19.data,
                                 q20=form.q20.data,
                                 q21=form.q21.data,
                                 q22=form.q22.data)
        db.session.add(review)
        db.session.commit()
        log = ActivityLog(
            log=f'Course {course.id}-{course.title} reviewed by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        course.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash(f'Review submitted for {course.title}.', 'alert-info')
        return redirect(url_for('continuing_medical_education'))
    return render_template('cme/cme_course_review.html', course=course, form=form)

