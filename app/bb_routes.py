from app import app
from app.bb_forms import *
from app.models import *
from app.bb_models import *
from app.email import *
from app.web_push_handler import *
from app.custom_decorators import course_admin_required, bb_admin_required, admin_required, user1_required

from flask import render_template, url_for, flash, redirect, request, make_response
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from time import time as ttime
from datetime import datetime, timedelta, time


@app.route('/bulletin_board', methods=['GET', 'POST'])
@login_required
def bulletin_board():
    bulletins = Bulletin.query.filter(Bulletin.approve_date.isnot(None), Bulletin.deleted.isnot(True)).order_by(
        Bulletin.approve_date.desc()).all()
    # .filter(
    #     Bulletin.designations.any(Designation.id == current_user.designation_id)).filter(
    #     Bulletin.departments.has(
    #         User.departments.any(bulletin_departments.c.department_id == user_departments.c.department_id))
    # )

    topics = BulletinTopic.query.order_by(BulletinTopic.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    designations = Designation.query.order_by(Designation.name.asc()).all()
    form = AddBulletinForm()
    form.topic.choices = [(0, 'Select Topic')] + [(t.id, t.name) for t in topics]
    form.departments.choices = [(0, 'Select Departments')] + [(1000, 'All Departments')] + [(d.id, d.name) for d in departments]
    form.designations.choices = [(0, 'Select Designations')] + [(1000, 'All Designations')] + [(d.id, d.name) for d in designations]
    if form.validate_on_submit():
        department_list = request.form.getlist('department_list')
        designation_list = request.form.getlist('designation_list')
        bulletin = Bulletin(title=form.title.data,
                            content=form.content.data,
                            topic_id=form.topic.data,
                            important=form.important.data,
                            submitted_by_id=current_user.id)
        db.session.add(bulletin)
        db.session.commit()
        for dept in department_list:
            if dept == 1000:
                for d in departments:
                    if d not in bulletin.departments:
                        bulletin.departments.append(d)
                        db.session.commit()
            else:
                b_department = Department.query.get(dept)
                if b_department and b_department not in bulletin.departments:
                    bulletin.departments.append(b_department)
                    db.session.commit()

        for desig in designation_list:
            if desig == 1000:
                for d in designations:
                    if d not in bulletin.designations:
                        bulletin.designations.append(d)
                        db.session.commit()
            else:
                b_designation = Designation.query.get(desig)
                if b_designation and b_designation not in bulletin.designations:
                    bulletin.designations.append(b_designation)
                    db.session.commit()
        if form.save.data:
            flash('Bulletin saved', 'alert-info')
            return redirect(url_for('my_bulletins'))
        elif form.add_attachment.data:
            return redirect(url_for('draft_bulletin', token=bulletin.get_id_token()))
        elif form.submit.data:
            bulletin.submitted_date = datetime.now()
            db.session.commit()
            push_json_admin = {"title": "Bulletin Submitted",
                               "body": f'{bulletin.title} bulletin was submitted by {bulletin.submitted_by.name}.'}
            trigger_push_notifications_for_bb_admins(push_json_admin)
            flash('Bulletin submitted and awaiting for approval', 'alert-info')
            return redirect(url_for('bulletin_board'))
    return render_template('bulletin_board/bb_index.html', form=form, bulletins=bulletins)


@app.route('/bulletin_board/bulletin/<token>', methods=['GET', 'POST'])
@login_required
def bulletin(token):
    bulletin = Bulletin.verify_id_token(token)
    if not bulletin:
        return redirect(url_for('bulletin_board'))
    if not bulletin.approve_date:
        return redirect(url_for('bulletin_board'))
    if current_user not in bulletin.viewer_list():
        viewer = BulletinViewer(bulletin_id=bulletin.id,
                                viewer_id=current_user.id,
                                view_date=datetime.now())
        db.session.add(viewer)
        db.session.commit()
    form = CommentForm()
    if form.validate_on_submit():
        comment = BulletinComment(bulletin_id=bulletin.id,
                                  comment=form.comment.data,
                                  submitted_by_id=current_user.id,
                                  submitted_date=datetime.now())
        db.session.add(comment)
        db.session.commit()
        flash('Comment submitted.', 'alert-info')
        return redirect(url_for('bulletin', token=bulletin.get_id_token()))
    return render_template('bulletin_board/bulletin.html', bulletin=bulletin, form=form)



@app.route('/bulletin_board/my_bulletins', methods=['GET', 'POST'])
@login_required
def my_bulletins():
    my_bulletins = Bulletin.query.filter_by(submitted_by_id=current_user.id).order_by(Bulletin.approve_date.desc()).all()
    topics = BulletinTopic.query.order_by(BulletinTopic.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    designations = Designation.query.order_by(Designation.name.asc()).all()
    form = AddBulletinForm()
    form.topic.choices = [(0, 'Select Topic')] + [(t.id, t.name) for t in topics]
    form.departments.choices = [(0, 'Select Departments')] + [(1000, 'All Departments')] + [(d.id, d.name) for d in
                                                                                            departments]
    form.designations.choices = [(0, 'Select Designations')] + [(1000, 'All Designations')] + [(d.id, d.name) for d in
                                                                                               designations]
    if form.validate_on_submit():
        department_list = request.form.getlist('department_list')
        designation_list = request.form.getlist('designation_list')
        bulletin = Bulletin(title=form.title.data,
                            content=form.content.data,
                            topic_id=form.topic.data,
                            important=form.important.data,
                            submitted_by_id=current_user.id)
        db.session.add(bulletin)
        db.session.commit()
        for dept in department_list:
            if dept == 1000:
                for d in departments:
                    if d not in bulletin.departments:
                        bulletin.departments.append(d)
                        db.session.commit()
            else:
                b_department = Department.query.get(dept)
                if b_department and b_department not in bulletin.departments:
                    bulletin.departments.append(b_department)
                    db.session.commit()

        for desig in designation_list:
            if desig == 1000:
                for d in designations:
                    if d not in bulletin.designations:
                        bulletin.designations.append(d)
                        db.session.commit()
            else:
                b_designation = Designation.query.get(desig)
                if b_designation and b_designation not in bulletin.designations:
                    bulletin.designations.append(b_designation)
                    db.session.commit()
        if form.save.data:
            return redirect(url_for('my_bulletins'))
        elif form.add_attachment.data:
            return redirect(url_for('draft_bulletin', token=bulletin.get_id_token()))
        elif form.submit.data:
            bulletin.submitted_date = datetime.now()
            db.session.commit()
            push_json_admin = {"title": "Bulletin Submitted",
                               "body": f'{bulletin.title} bulletin was submitted by {bulletin.submitted_by.name}.'}
            trigger_push_notifications_for_bb_admins(push_json_admin)
            return redirect(url_for('bulletin_board'))
    return render_template('bulletin_board/draft_bulletins.html', my_bulletins=my_bulletins, form=form)


@app.route('/bulletin_board/draft_bulletin/<token>', methods=['GET', 'POST'])
@login_required
def draft_bulletin(token):
    draft_bulletin = Bulletin.verify_id_token(token)
    if not draft_bulletin:
        return redirect(url_for('bulletin_board'))
    if not draft_bulletin.submitted_by_id == current_user.id:
        return redirect(url_for('bulletin_board'))
    topics = BulletinTopic.query.order_by(BulletinTopic.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    designations = Designation.query.order_by(Designation.name.asc()).all()
    form = EditBulletinForm()
    form.topic.choices = [(0, 'Select Topic')] + [(t.id, t.name) for t in topics]
    form.departments.choices = [(0, 'Select Departments')] + [(1000, 'All Departments')] + [(d.id, d.name) for d in
                                                                                            departments]
    form.designations.choices = [(0, 'Select Designations')] + [(1000, 'All Designations')] + [(d.id, d.name) for d in
                                                                                               designations]
    if form.validate_on_submit():
        draft_bulletin.title = form.title.data
        draft_bulletin.content=form.content.data
        draft_bulletin.topic_id=form.topic.data
        draft_bulletin.important=form.important.data
        department_list = request.form.getlist('department_list')
        designation_list = request.form.getlist('designation_list')
        db.session.commit()
        for dept in department_list:
            if int(dept) == 1000:
                for d in departments:
                    if d not in draft_bulletin.departments:
                        draft_bulletin.departments.append(d)
                        db.session.commit()
            else:
                b_department = Department.query.get(dept)
                if b_department and b_department not in draft_bulletin.departments:
                    draft_bulletin.departments.append(b_department)
                    db.session.commit()

        for desig in designation_list:
            if int(desig) == 1000:
                for d in designations:
                    if d not in draft_bulletin.designations:
                        draft_bulletin.designations.append(d)
                        db.session.commit()
            else:
                b_designation = Designation.query.get(desig)
                if b_designation and b_designation not in draft_bulletin.designations:
                    draft_bulletin.designations.append(b_designation)
                    db.session.commit()
        if form.save.data:
            return redirect(url_for('draft_bulletin', token=draft_bulletin.get_id_token()))

        elif form.submit.data:
            draft_bulletin.submitted_date = datetime.now()
            db.session.commit()

            push_json_admin = {"title": "Bulletin Submitted",
                               "body": f'{draft_bulletin.title} bulletin was submitted by {draft_bulletin.submitted_by.name}.'}
            trigger_push_notifications_for_bb_admins(push_json_admin)
            return redirect(url_for('bulletin_board'))
    elif request.method == 'GET':
        form.title.data = draft_bulletin.title
        form.content.data = draft_bulletin.content
        form.topic.data = draft_bulletin.topic_id
        form.important.data = draft_bulletin.important
    return render_template('bulletin_board/draft_bulletin_attachment.html', draft_bulletin=draft_bulletin, form=form)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4']


@app.route('/learning_hub/bulletin/upload_attachments/<token>', methods=['POST'])
@login_required
def bulletin_upload_attachments(token):
    bulletin = Bulletin.verify_id_token(token)
    if not bulletin:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('bulletin_board'))
    if bulletin.submitted_by_id != current_user.id:
        return redirect(url_for('bulletin_board'))

    file = request.files['file']
    print(allowed_file(file.filename))
    if allowed_file(file.filename):
        filename_ = secure_filename(file.filename)
        filename = f'bulletin_{bulletin.id}_{filename_}'#datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S-') + filename_
        save_path = os.path.join('app/static/bulletin/', filename)
        filetype = filename.rsplit('.', 1)[1].lower()
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
                bulletin_attachment = BulletinAttachment(filepath=f'bulletin/{filename}',
                                                         filename=filename_,
                                                         filetype=filetype,
                                                         bulletin_id=bulletin.id)
                db.session.add(bulletin_attachment)
                db.session.commit()
                log = ActivityLog(
                    log=f'{bulletin_attachment.id}-{bulletin_attachment.filepath} added by {current_user.id}-{current_user.name}')
                db.session.add(log)
                db.session.commit()
                bulletin_attachment.logs.append(log)
                current_user.logs.append(log)
                db.session.commit()
        else:
            print(f'Chunk {current_chunk + 1} of {total_chunks} '
                      f'for file {file.filename} complete')
            return make_response(("Chunk upload successful", 200))
        return make_response(('Uploaded Chunk', 200))
    else:
        return make_response(('File not allowed', 400))


@app.route('/learning_hub/bulletin/delete_attachment/<token>', methods=['POST'])
@login_required
def bulletin_delete_attachment(token):
    bulletin_attachment = BulletinAttachment.verify_id_token(token)
    if not bulletin_delete_attachment:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('bulletin_board'))
    if bulletin_delete_attachment.bulletin.submitted_by_id != current_user.id:
        return redirect(url_for('bulletin_board'))
    bulletin_attachment.deleted = True
    db.session.commit()
    log = ActivityLog(
        log=f'{bulletin_attachment.id}-{bulletin_attachment.filepath} deleted by {current_user.id}-{current_user.name}')
    db.session.add(log)
    db.session.commit()
    bulletin_attachment.logs.append(log)
    current_user.logs.append(log)
    db.session.commit()
    return redirect(url_for('draft_bulletin', token=bulletin_attachment.bulletin.get_id_token()))