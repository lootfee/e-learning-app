from app import app
from flask import render_template, url_for, flash, redirect, request, make_response
from app.models import User, Designation
from app.cme_models import *
from app.cme_forms import *
from app.email import *
from app.web_push_handler import *
from app.custom_decorators import course_admin_required, admin_required, course_creator_required
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from gtts import gTTS


from time import time as ttime
from datetime import datetime, timedelta, time
import calendar
import statistics


def allowed_cme_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def allowed_cme_video(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mp4', 'mov', 'wmv', 'avi', 'flv'}


@app.route('/learning_hub/admin', methods=['GET', 'POST'])
@login_required
def cme_admin():
    return redirect(url_for('cme_manage_courses'))


@app.route('/learning_hub/topics', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_topics():
    # if current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    topics = CmeCourseTopic.query.order_by(CmeCourseTopic.name.asc()).all()
    form = AddTopicForm()
    if form.validate_on_submit():
        topic = CmeCourseTopic(name=form.name.data)
        db.session.add(topic)
        db.session.commit()
        log = ActivityLog(log=f'{topic.id}-{topic.name} added by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        topic.logs.append(log)
        db.session.commit()
        flash(f'{topic.name} topic category added', 'alert-info')
        return redirect(url_for('cme_topics'))
    return render_template('cme_admin/topics.html', form=form, topics=topics)


@app.route('/learning_hub/manage_courses', methods=['GET', 'POST'])
@login_required
@course_creator_required
def cme_manage_courses():
    # if current_user.is_cme_course_creator() == False and current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    courses = CmeCourse.query.order_by(CmeCourse.presentation_date.desc()).all()
    users = User.query.all()
    form = EditCourseForm()
    topics = CmeCourseTopic.query.order_by(CmeCourseTopic.name.asc()).all()
    form.topic_id.choices = [(0, 'Select Topic')] + [(u.id, u.name) for u in topics]
    form.presented_by1.choices = [(0, 'Select User')] + [(u.id, u.name) for u in users]
    form.presented_by2.choices = [(0, 'Select User')] + [(u.id, u.name) for u in users]
    form.presented_by3.choices = [(0, 'Select User')] + [(u.id, u.name) for u in users]
    if form.submit.data:
        if form.validate_on_submit():
            course = CmeCourse.query.get(form.course_id.data)
            file = form.cover_page.data
            if file and allowed_cme_file(file.filename):
                filename_ = secure_filename(file.filename)
                filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-') + filename_
                file.save(os.path.join('app/static/cme', filename))
                os.remove('app/static/cme/' + course.cover_page)
                course.cover_page = filename
            course.title = form.title.data
            course.topic_id = form.topic_id.data
            # course.presented_by_id = form.presented_by.data,
            course.deadline = form.deadline.data,
            # course.cme_points = form.cme_points.data,
            # course.cme_serial_no = form.cme_serial_no.data,
            course.published = False
            presented_by1 = User.query.get(form.presented_by1.data)
            course.creators.append(presented_by1)
            if form.presented_by2.data != 0:
                presented_by2 = User.query.get(form.presented_by2.data)
                course.creators.append(presented_by2)
            if form.presented_by3.data != 0:
                presented_by3 = User.query.get(form.presented_by3.data)
                course.creators.append(presented_by3)
            db.session.commit()

            log = ActivityLog(log=f'{course.id}-{course.title} topic-{course.topic_id}-{course.topic.name} '
                                  f'deadline-{course.deadline} coverpage-{course.cover_page} '
                                  f'creators-{[(creator.id, creator.name) for creator in course.creators]} '
                                  f'updated by {current_user.id}-{current_user.name}',
                              date=datetime.now())
            db.session.add(log)
            db.session.commit()
            course.logs.append(log)
            db.session.commit()
            flash(course.title + ' course details edited', 'alert-info')
            return redirect(url_for('cme_manage_courses'))

    # changed to auto publish upon course publish since doh not required anymore
    # cert_form = PublishCertificateForm()
    # if cert_form.cert_submit.data:
    #     if cert_form.validate_on_submit():
    #         cert_course = CmeCourse.query.get(cert_form.cert_course_id.data)
    #         cert_course.cme_points = cert_form.cme_points.data
    #         cert_course.cme_serial_no = cert_form.cme_serial_no.data
    #         db.session.commit()
    #         flash('Course certificates published', 'alert-info')
    return render_template('cme_admin/manage_courses.html', courses=courses, form=form) # , cert_form=cert_form


@app.route('/learning_hub/add_course', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_add_course():
    # if current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    form = AddCourseForm()
    users = User.query.order_by(User.name.asc()).all()
    topics = CmeCourseTopic.query.order_by(CmeCourseTopic.name.asc()).all()
    form.topic_id.choices = [(0, 'Select Topic')] + [(u.id, u.name) for u in topics]
    form.presented_by1.choices = [(0, 'Select User')] + [(u.id, u.name) for u in users]
    form.presented_by2.choices = [(0, 'Select User')] + [(u.id, u.name) for u in users]
    form.presented_by3.choices = [(0, 'Select User')] + [(u.id, u.name) for u in users]
    if form.validate_on_submit():
        file = form.cover_page.data
        if allowed_cme_file(file.filename):
            filename_ = secure_filename(file.filename)
            filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-') + filename_
            file.save(os.path.join('app/static/cme/', filename))
            new_course = CmeCourse(title=form.title.data,
                                   cover_page=filename,
                                   deadline=form.deadline.data,
                                   topic_id=form.topic_id.data,
                                   # cme_points=form.cme_points.data,
                                   # cme_serial_no=form.cme_serial_no.data,
                                   published=False)
            presented_by1 = User.query.get(form.presented_by1.data)
            if presented_by1:
                db.session.add(new_course)
                db.session.commit()
                new_course.creators.append(presented_by1)
                if form.presented_by2.data != 0:
                    presented_by2 = User.query.get(form.presented_by2.data)
                    new_course.creators.append(presented_by2)
                if form.presented_by3.data != 0:
                    presented_by3 = User.query.get(form.presented_by3.data)
                    new_course.creators.append(presented_by3)
                db.session.commit()

                push_json = {"title": f"Course Created",
                             "body": f'{new_course.title} course has been created by {current_user.name}. '
                                     f'You can access it thru the Training and Development App admin panel.',
                             }  # "data": {"html": url_for('index')}

                for user in new_course.creators:
                    trigger_push_notifications_for_user(push_json, user)
                log = ActivityLog(
                    log=f'{new_course.id}-{new_course.title} topic-{new_course.topic_id}-{new_course.topic.name} '
                        f'deadline-{new_course.deadline} coverpage-{new_course.cover_page} '
                        f'creators-{[(creator.id, creator.name) for creator in new_course.creators]} '
                        f'added by {current_user.id}-{current_user.name}',
                    date=datetime.now())
                db.session.add(log)
                db.session.commit()
                new_course.logs.append(log)
                db.session.commit()
                flash(new_course.title + ' course added.', 'alert-info')
                return redirect(url_for('cme_add_course_content', token=new_course.get_id_token()))
            else:
                flash('Please select a course presenter!', 'alert-info')
                return redirect(url_for('cme_add_course'))
    return render_template('cme_admin/add_course.html', form=form)


@app.route('/learning_hub/delete_course/<token>', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_delete_course(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    # if course.is_creator(current_user) == False and current_user.designation_id > 1:
    #     return redirect(url_for('continuing_medical_education'))
    # db.session.delete(course)
    course.deleted = True
    db.session.commit()
    log = ActivityLog(
        log=f'{course.id}-{course.title} deleted by {current_user.id}-{current_user.name},',
        date=datetime.now())
    db.session.add(log)
    db.session.commit()
    course.logs.append(log)
    db.session.commit()
    return redirect(url_for('cme_manage_courses'))


@app.route('/learning_hub/manage_course_content/<token>', methods=['GET', 'POST'])
@login_required
def cme_add_course_content(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))
    form = AddCourseContentForm()
    if form.validate_on_submit():
        content = CmeCourseContent(title=form.title.data,
                                   index=form.index.data,
                                   course_id=course.id)
        db.session.add(content)
        db.session.commit()
        log = ActivityLog(
            log=f'{content.id}-{content.title} index-{content.index} added by {current_user.id}-{current_user.name}',
            date=datetime.now())
        db.session.add(log)
        db.session.commit()
        content.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash('Content ' + content.title + ' added', 'alert-info')
        return redirect(url_for('cme_add_course_content_slides', token=content.get_id_token()))
    edit_form = EditCourseContentForm()
    if edit_form.validate_on_submit():
        edit_content = CmeCourseContent.verify_id_token(edit_form.content_id.data)
        edit_content.title = edit_form.edit_title.data
        edit_content.index = edit_form.edit_index.data
        db.session.commit()
        log = ActivityLog(
            log=f'{edit_content.id}-{edit_content.title} index-{edit_content.index} '
                f'edited by {current_user.id}-{current_user.name}',
            date=datetime.now())
        db.session.add(log)
        db.session.commit()
        edit_content.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash('Content ' + edit_content.title + 'edited.', 'alert-info')
        return redirect(url_for('cme_add_course_content', token=edit_content.get_id_token()))
    return render_template('cme_admin/add_course_content.html', course=course, form=form, edit_form=edit_form)


@app.route('/learning_hub/delete_course_content/<token>', methods=['GET', 'POST'])
@login_required
def cme_delete_course_content(token):
    content = CmeCourseContent.verify_id_token(token)
    if not content:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if content.course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))
    # db.session.delete(content)
    content.deleted = True
    db.session.commit()
    log = ActivityLog(
        log=f'{content.id}-{content.title} deleted by {current_user.id}-{current_user.name}')
    db.session.add(log)
    db.session.commit()
    content.logs.append(log)
    current_user.logs.append(log)
    db.session.commit()
    flash(content.title + ' deleted!', 'alert-info')
    return redirect(url_for('cme_add_course_content', token=content.get_id_token()))


@app.route('/learning_hub/add_course_content_slides/<token>', methods=['GET', 'POST'])
@login_required
def cme_add_course_content_slides(token):
    content = CmeCourseContent.verify_id_token(token)
    if not content:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if content.course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))
    form = AddContentSlideForm()
    edit_form = EditContentSlideForm()
    # video_form = AddContentVideoForm()
    if form.submit.data:
        if form.validate_on_submit():
            file = form.image_file.data
            if allowed_cme_file(file.filename):
                filename_ = secure_filename(file.filename)
                filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-') + filename_
                file.save(os.path.join('app/static/cme/', filename))

                tts = gTTS(form.slide_text.data)
                tts_filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S-tts') + '.mp3'
                tts.save('app/static/cme/' + tts_filename)
                slide = CmeContentSlides(image_file=filename,
                                         sound_file=tts_filename,
                                         slide_text=form.slide_text.data,
                                         index=form.index.data,
                                         course_id=content.course_id,
                                         course_content_id=content.id)
                db.session.add(slide)
                db.session.commit()
                log = ActivityLog(
                    log=f'slide-{slide.id} image-file-{slide.image_file} sound-file-{slide.sound_file} '
                        f'text-{slide.slide_text} index-{slide.index} course-id-{slide.course_id} course-content-id-{slide.course_content_id}'
                        f'added by {current_user.id}-{current_user.name}')
                db.session.add(log)
                db.session.commit()
                slide.logs.append(log)
                current_user.logs.append(log)
                db.session.commit()
                flash('Slide has been added', 'alert-info')
            return redirect(url_for('cme_add_course_content_slides', token=content.get_id_token()))
    if edit_form.edit_submit.data:
        if edit_form.validate_on_submit():
            edit_slide = CmeContentSlides.query.get(edit_form.slide_id.data)

            if edit_form.edit_image_file.data:
                os.remove('app/static/cme/' + edit_slide.image_file)

                file = edit_form.edit_image_file.data
                if allowed_cme_file(file.filename):
                    filename_ = secure_filename(file.filename)
                    filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S-') + filename_
                    file.save(os.path.join('app/static/cme/', filename))
                    edit_slide.image_file = filename

            os.remove('app/static/cme/' + edit_slide.sound_file)
            tts = gTTS(edit_form.edit_slide_text.data)
            tts_filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S-tts') + '.mp3'
            tts.save('app/static/cme/' + tts_filename)

            edit_slide.slide_text = edit_form.edit_slide_text.data
            edit_slide.sound_file = tts_filename
            edit_slide.index = edit_form.edit_index.data
            db.session.commit()
            log = ActivityLog(
                log=f'slide-{edit_slide.id} image-file-{edit_slide.image_file} sound-file-{edit_slide.sound_file} '
                    f'text-{edit_slide.slide_text} index-{edit_slide.index} course-id-{edit_slide.course_id} course-content-id-{edit_slide.course_content_id}'
                    f'added by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            edit_slide.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()
            flash('Slide has been edited', 'alert-info')
            return redirect(url_for('cme_add_course_content_slides', token=content.get_id_token()))

    # if video_form.video_submit.data:
    #     if video_form.validate_on_submit():
    #         file = video_form.video_file.data
    #         if allowed_cme_video(file.filename):
    #
    #             filename_ = secure_filename(file.filename)
    #             filename = datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S-') + filename_
    #             file.save(os.path.join('app/static/cme/', filename))
    #
    #             slide = CmeContentSlides(sound_file=filename,
    #                                      index=video_form.video_index.data,
    #                                      course_id=content.course_id,
    #                                      course_content_id=content.id)
    #             db.session.add(slide)
    #             db.session.commit()
    #             flash('Video has been added', 'alert-info')
    #             return redirect(url_for('cme_add_course_content_slides', token=content.get_id_token()))

    return render_template('cme_admin/add_content_slides.html', content=content, form=form, edit_form=edit_form)


@app.route('/learning_hub/upload_video/<token>', methods=['POST'])
@login_required
def cme_upload_video(token):
    content = CmeCourseContent.verify_id_token(token)
    if not content:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if content.course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))

    file = request.files['file']
    filename_ = secure_filename(file.filename)
    filename = f'video_{content.id}_{filename_}'#datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S-') + filename_
    save_path = os.path.join('app/static/cme/', filename)
    current_chunk = int(request.form['dzchunkindex'])
    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))

    try:
        with open(save_path, 'ab') as f:
            f.seek(int(request.form['dzchunkbyteoffset']))
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong
        # log.exception('Could not write to file')
        return make_response(("Not sure why,"
                              " but we couldn't write the file to disk", 500))

    total_chunks = int(request.form['dztotalchunkcount'])
    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        if os.path.getsize(save_path) != int(request.form['dztotalfilesize']):
            # log.error(f"File {file.filename} was completed, "
            #           f"but has a size mismatch."
            #           f"Was {os.path.getsize(save_path)} but we"
            #           f" expected {request.form['dztotalfilesize']} ")
            print(f"File {file.filename} was completed, "
                      f"but has a size mismatch."
                      f"Was {os.path.getsize(save_path)} but we"
                      f" expected {request.form['dztotalfilesize']} ")
            return make_response(('Size mismatch', 500))
        else:
            print(f'File {file.filename} has been uploaded successfully')
            video_file = CmeContentVideo(video_file=filename,
                                     course_id=content.course_id,
                                     course_content_id=content.id)
            db.session.add(video_file)
            db.session.commit()
            log = ActivityLog(
                log=f'{video_file.id}-{video_file.video_file} added by {current_user.id}-{current_user.name}')
            db.session.add(log)
            db.session.commit()
            video_file.logs.append(log)
            current_user.logs.append(log)
            db.session.commit()
    else:
        print(f'Chunk {current_chunk + 1} of {total_chunks} '
                  f'for file {file.filename} complete')
        return make_response(("Chunk upload successful", 200))
    return make_response(('Uploaded Chunk', 200))


@app.route('/learning_hub/delete_content_slide/<token>', methods=['GET', 'POST'])
@login_required
def cme_delete_content_slide(token):
    slide = CmeContentSlides.verify_id_token(token)
    if not slide:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if slide.course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))
    # db.session.delete(slide)
    slide.deleted = True
    db.session.commit()
    log = ActivityLog(
        log=f'slide-{slide.id} deleted by {current_user.id}-{current_user.name}')
    db.session.add(log)
    db.session.commit()
    slide.logs.append(log)
    current_user.logs.append(log)
    db.session.commit()
    # os.remove(f'app/static/cme/{slide.image_file}')
    # os.remove(f'app/static/cme/{slide.sound_file}')
    flash('Slide deleted!', 'alert-info')
    return redirect(url_for('cme_add_course_content_slides', token=slide.course_content.get_id_token()))


@app.route('/learning_hub/delete_content_video/<token>', methods=['GET', 'POST'])
@login_required
def cme_delete_content_video(token):
    video = CmeContentVideo.verify_id_token(token)
    if not video:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if video.course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))

    # db.session.delete(video)
    video.deleted = True
    db.session.commit()
    log = ActivityLog(
        log=f'video-{video.id} deleted by {current_user.id}-{current_user.name}')
    db.session.add(log)
    db.session.commit()
    video.logs.append(log)
    current_user.logs.append(log)
    db.session.commit()
    # os.remove(f'app/static/cme/{video.video_file}')
    flash('Video deleted!', 'alert-info')
    return redirect(url_for('cme_add_course_content_slides', token=video.course_content.get_id_token()))


@app.route('/learning_hub/manage_exam/<token>', methods=['GET', 'POST'])
@login_required
def cme_manage_exam(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))
    form = AddQuestionForm()
    if form.validate_on_submit():
        question = CmeCourseQuestion(title=form.question.data,
                                     answer_explanation=form.answer_explanation.data,
                                     course_id=course.id)
        db.session.add(question)
        db.session.commit()

        ans = request.form.get('question_radios')
        for i in range(1, 10):
            answer = False
            if i == int(ans):
                answer = True
            choice_ = request.form.get('option' + str(i))
            if choice_:
                choice = CmeCourseQuestionChoices(title=choice_,
                                                  answer=answer,
                                                  question_id=question.id,
                                                  course_id=course.id)
                db.session.add(choice)
                db.session.commit()
        log = ActivityLog(
            log=f'question-{question.id}-{question.title} explanation-{question.answer_explanation} '
                f'choices-{[(c.id, c.title, c.answer) for c in question.choices]} '
                f'added by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        question.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash('Question saved', 'alert-info')
        return redirect(url_for('cme_manage_exam', token=course.get_id_token()))

    edit_form = EditQuestionForm()
    if edit_form.validate_on_submit():
        edit_question = CmeCourseQuestion.query.get(edit_form.question_id.data)
        edit_question.title = edit_form.edit_question.data
        edit_question.answer_explanation = edit_form.edit_answer_explanation.data
        if edit_question.choices:
            for ec in edit_question.choices:
                db.session.delete(ec)
        ans = request.form.get('question_radios')
        for i in range(1, 10):
            answer = False
            if i == int(ans):
                answer = True
            choice_ = request.form.get('option' + str(i))
            if choice_:
                choice = CmeCourseQuestionChoices(title=choice_,
                                                  answer=answer,
                                                  question_id=edit_question.id,
                                                  course_id=course.id)
                db.session.add(choice)
                db.session.commit()
        log = ActivityLog(
            log=f'question-{edit_question.id}-{edit_question.title} explanation-{edit_question.answer_explanation} '
                f'choices-{[(c.id, c.title, c.answer) for c in edit_question.choices]} '
                f'edited by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        edit_question.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash('Question saved', 'alert-info')
        return redirect(url_for('cme_manage_exam', token=course.get_id_token()))

    return render_template('cme_admin/manage_exam.html', course=course, form=form, edit_form=edit_form)


@app.route('/learning_hub/get_question_choices', methods=['GET', 'POST'])
@login_required
def cme_get_question_choices():
    question_id = request.args.get('question_id')
    question = CmeCourseQuestion.verify_id_token(question_id)

    if not question:
        return "Invalid token"
    if question.course.is_creator(current_user) == False:
        return "Invalid access"
    question_data = {
        'title': question.title,
        'answer_explanation': question.answer_explanation,
        'choices': [],
        'answer': ''
    }
    for choice in question.choices:
        if choice.answer == True:
            question_data['answer'] = choice.id
        question_data['choices'].append(
            {'title': choice.title,
             'id': choice.id}
        )

    return jsonify(question_data)


@app.route('/learning_hub/delete_course_question/<token>', methods=['GET', 'POST'])
@login_required
def delete_exam_question(token):
    question = CmeCourseQuestion.verify_id_token(token)
    if not question:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if question.course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))
    db.session.delete(question)
    db.session.commit()
    log = ActivityLog(
        log=f'question-{question.id}-{question.title} deleted by {current_user.id}-{current_user.name}')
    db.session.add(log)
    db.session.commit()
    question.logs.append(log)
    current_user.logs.append(log)
    db.session.commit()
    flash('Question deleted!', 'alert-info')
    return redirect(url_for('cme_manage_exam', token=question.course.get_id_token()))


@app.route('/learning_hub/publish_course/<token>', methods=['GET', 'POST'])
@login_required
def cme_publish_course(token):
    course = CmeCourse.verify_id_token(token)
    if not course:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('index'))
    if course.is_creator(current_user) == False:
        return redirect(url_for('continuing_medical_education'))

    # verify that course content index is complete
    content_index_ = sorted([(content.index) for content in course.contents])
    for i, e in enumerate(content_index_):
        if e - 1 != i:
            flash('Missing index number in course chapters.', 'alert-warning')
            return redirect(url_for('cme_add_course_content', token=course.get_id_token()))
    if not course.questions:
        flash('Please add course pre/post test questions.', 'alert-warning')
        return redirect(url_for('cme_add_course_content', token=course.get_id_token()))
    if course.published == False:
        course.published = True
        course.published_date = datetime.now()
        db.session.commit()

        push_json = {"title": f"New Course Published",
                     "body": f'{course.title} course has been published on the Training and Development App.',
                     }
        trigger_push_notifications_for_all(push_json)
        log = ActivityLog(
            log=f'{course.id}-{course.title} published by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        course.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash(course.title + ' published.', 'alert-info')
        return redirect(url_for('cme_add_course_content', token=course.get_id_token()))
    elif course.published == True:
        course.published = False
        course.published_date = None
        db.session.commit()
        log = ActivityLog(
            log=f'{course.id}-{course.title} unpublished by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        course.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash(course.title + ' unpublished.', 'alert-info')
        return redirect(url_for('cme_add_course_content', token=course.get_id_token()))


@app.route('/learning_hub/dashboards', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_dashboards():
    # if not current_user.is_cme_admin():
    #     return redirect(url_for('continuing_medical_education'))
    year = datetime.now().year
    return redirect(url_for('cme_dashboard_annual_plan', year=year))


@app.route('/learning_hub/dashboards/dashboard_annual_plan/<int:year>', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_dashboard_annual_plan(year):
    # if not current_user.is_cme_admin():
    #     return redirect(url_for('continuing_medical_education'))
    current_year = year
    years = list(range(datetime.now().year, 2020, -1))
    # current_month = month
    months = [{'id': i + 1, 'name': calendar.month_abbr[i + 1]} for i in range(12)]
    # current_month_name = calendar.month_name[current_month]
    topics = CmeCourseTopic.query.order_by(CmeCourseTopic.name.asc()).all()
    return render_template('cme_admin/dashboard_annual_plan.html', current_year=current_year, years=years,
                           months=months, topics=topics)


@app.route('/learning_hub/dashboards/courses_summary/<int:year>/<int:month>', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_courses_summary(year, month):
    # if current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    current_year = year
    years = list(range(datetime.now().year, 2020, -1))
    current_month = month
    months = [{'id': i + 1, 'name': calendar.month_abbr[i + 1]} for i in range(12)]
    current_month_name = calendar.month_name[current_month]

    courses = CmeCourse.query.filter(extract('year', CmeCourse.deadline) == year,
                                     extract('month', CmeCourse.deadline) == month).order_by(CmeCourse.deadline.asc()).all()
    return render_template('cme_admin/dashboard_courses_summary.html', current_year=current_year, years=years,
                           current_month=current_month, months=months, current_month_name=current_month_name, courses=courses)


@app.route('/learning_hub/dashboards/attendance_record/<token>', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_attendance_record(token):
    # if current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    course = CmeCourse.verify_id_token(token)
    if not course:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('cme_dashboards'))
    return render_template('cme_admin/dashboard_attendance_record.html', course=course)


@app.route('/learning_hub/dashboards/consolidated_report/<token>', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_consolidated_report(token):
    # if current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    course = CmeCourse.verify_id_token(token)
    if not course:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('cme_dashboards'))
    post_tests = len(course.post_tests)
    post_pass = 0
    for post in course.post_tests:
        if post.passed():
            post_pass += 1
    post_fail = post_tests - post_pass
    return render_template('cme_admin/dashboard_consolidated_report.html', course=course, post_pass=post_pass, post_fail=post_fail)


@app.route('/learning_hub/dashboards/employees_summary/<int:year>', methods=['GET', 'POST'])
@login_required
@course_admin_required
def cme_employees_summary(year):
    # if current_user.designation_id != 1:
    #     return redirect(url_for('continuing_medical_education'))
    current_year = year
    years = list(range(datetime.now().year, 2020, -1))
    courses = CmeCourse.query.filter(extract('year', CmeCourse.deadline) == current_year).all()
    users = User.query.order_by(User.name.asc()).all()
    for u in users:
        u.pre_scores = []
        u.post_scores = []

        u.pre_tests = CmeCoursePreTest.query.filter_by(user_id=u.id).join(CmeCourse).filter(
            extract('year', CmeCourse.deadline) == current_year).all()
        for pre in u.pre_tests:
            u.pre_scores.append(pre.percent_score())
        try:
            u.pre_avg = statistics.mean(u.pre_scores)
        except statistics.StatisticsError:
            u.pre_avg = None
        u.post_tests = CmeCoursePostTest.query.filter_by(user_id=u.id).join(CmeCourse).filter(
            extract('year', CmeCourse.deadline) == current_year).all()
        post_filter = {}
        for post in u.post_tests:
            if post.passed():
                post_filter[post.course_id] = post.percent_score()

        for i, e in enumerate(post_filter):
            u.post_scores.append(post_filter[e])
        try:
            u.post_avg = statistics.mean(u.post_scores)
        except statistics.StatisticsError:
            u.post_avg = None

    return render_template('cme_admin/dashboard_employee_summary.html', current_year=current_year, years=years, users=users, courses=courses)


@app.route('/learning_hub/dashboards/employee/<token>/<int:year>', methods=['GET', 'POST'])
@login_required
def cme_employee(token, year):
    user = User.verify_id_token(token)
    if not user:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('cme_dashboards'))
    current_year = year
    years = list(range(datetime.now().year, 2020, -1))
    courses = CmeCourse.query.filter(extract('year', CmeCourse.deadline) == current_year).all()
    return render_template('cme_admin/dashboard_employee.html', user=user, current_year=current_year, years=years, courses=courses)
