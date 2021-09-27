from app import app
from flask import render_template, url_for, flash, redirect, request
from app.bb_forms import *
from app.bb_models import *
from app.models import *
from app.email import *
from app.service_worker import *
from app.custom_decorators import course_admin_required, bb_admin_required, admin_required, user1_required
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from time import time as ttime
from datetime import datetime, timedelta, time


@app.route('/bulletin_board_admin', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def bulletin_admin():
    users = User.query.all()
    designations = Designation.query.all()
    return render_template('bulletin_board_admin/bb_admin_index.html', users=users, designations=designations)
    # if current_user.id == 1 or current_user.designation_id <= 2 if current_user.designation_id else None:
    #     users = User.query.all()
    #     designations = Designation.query.all()
    #     return render_template('bulletin_board_admin/bb_admin_index.html', users=users, designations=designations)
    # else:
    #     redirect(url_for('index'))


@app.route('/bulletin_board_admin/designation', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def designation():
    designations = Designation.query.order_by(Designation.name.asc()).all()
    form = AddDesignationForm()
    if form.validate_on_submit():
        designation = Designation(name=form.name.data)
        db.session.add(designation)
        log = ActivityLog(log=f'Designation {form.name.data} added by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        designation.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return redirect(url_for('designation'))
    return render_template('bulletin_board_admin/designation.html', designations=designations, form=form)


@app.route('/bulletin_board_admin/department', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def department():
    departments = Department.query.order_by(Department.name.asc()).all()
    form = AddDepartmentForm()
    if form.validate_on_submit():
        department = Department(name=form.name.data)
        db.session.add(department)
        log = ActivityLog(log=f'Department {form.name.data} added by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        department.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return redirect(url_for('department'))
    return render_template('bulletin_board_admin/department.html', departments=departments, form=form)


@app.route('/bulletin_board_admin/bulletin_board/topics', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def bb_topics():
    topics = BulletinTopic.query.order_by(BulletinTopic.name.asc()).all()
    form = AddTopicForm()
    if form.validate_on_submit():
        topic = BulletinTopic(name=form.name.data)
        db.session.add(topic)
        log = ActivityLog(log=f'Topic {form.name.data} added by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        topic.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        return redirect(url_for('bb_topics'))
    return render_template('bulletin_board_admin/topic.html', topics=topics, form=form)


@app.route('/bulletin_board_admin/role', methods=['GET', 'POST'])
@login_required
@user1_required
def role():
    roles = Role.query.order_by(Role.name.asc()).all()
    form = AddRoleForm()
    if form.validate_on_submit():
        role = Role(name=form.name.data)
        db.session.add(role)
        log = ActivityLog(log=f'Role {form.name.data} added by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        role.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        flash(f'{role.name} added', 'alert-info')
        return redirect(url_for('role'))
    return render_template('bulletin_board_admin/role.html', roles=roles, form=form)


@app.route('/bulletin_board_admin/users', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def users():
    # if current_user.id != 1 or current_user.designation_id > 2 if current_user.designation_id else None:
    #     return redirect(url_for('index'))
    users = User.query.order_by(User.name.asc()).all()
    designations = Designation.query.order_by(Designation.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    form = AddUserForm()
    form.designation.choices = [(0, 'Select Designation')] + [(d.id, d.name) for d in designations]
    form.department.choices = [(0, 'Select Department')] + [(d.id, d.name) for d in departments]
    if form.validate_on_submit():
        new_user = User(name=form.name.data,
                        email=form.email.data.lower().replace(' ', ''),
                        designation_id=form.designation.data)
        db.session.add(new_user)
        db.session.commit()
        department = Department.query.get(form.department.data)
        new_user.departments.append(department)
        log = ActivityLog(log=f'{new_user.id}-{new_user.name} added by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        new_user.logs.append(log)
        db.session.commit()

        user_activation = UserActivation(user_id=new_user.id, date_activated=datetime.now())
        activation_log = ActivityLog(log=f'{new_user.id}-{new_user.name} activated by {current_user.id}-{current_user.name}',
                                     date=datetime.now())
        db.session.add(user_activation)
        db.session.add(activation_log)
        db.session.commit()
        user_activation.logs.append(activation_log)
        db.session.commit()

        body = f'You have been registered on the Biogenix - Learning Hub app by ' \
               f'{current_user.name} with the designation of {new_user.designation.name} under department {new_user.department.name}.'
        email_user(new_user.id, 'User registration', body)
        push_json = {"title": "User registration",
                     "body": f'{new_user.name} was registered on the Training and Development app with email {new_user.email} by {current_user.name}.'}
        trigger_push_notifications_for_bb_admins(push_json)

        flash(f'{new_user.name} has been successfully registered.', 'alert-info')
        return redirect(url_for('users'))

    return render_template('bulletin_board_admin/users.html', users=users, form=form)


@app.route('/bulletin_board_admin/update_user_role/<token>', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def update_user_role(token):
    user = User.verify_id_token(token)
    if not user:
        flash('Token expired', 'alert-warning')
        return redirect(url_for('bulletin_admin'))
    designations = Designation.query.order_by(Designation.name.asc()).all()
    departments = Department.query.order_by(Department.name.asc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    form = EditUserDesignationForm()
    form.designation.choices = [(0, 'Select Designation')] + [(d.id, d.name) for d in designations]
    form.activation.choices = [(1, 'Active'), (0, 'Inactive')]

    if form.validate_on_submit():
        if form.designation.data != user.designation_id:
            user.designation_id = form.designation.data
            db.session.commit()
            designation_log = ActivityLog(
                log=f' {user.id}-{user.name} designation changed to {user.designation_id}-{user.designation.name}',
                date=datetime.now())
            db.session.add(designation_log)
            db.session.commit()
            user.logs.append(designation_log)
            db.session.commit()
            push_json = {"title": "User Designation Update",
                         "body": f'Your designation has been updated to {user.designation.name} by {current_user.name}.'
                         }  # "data": {"html": url_for('index')}
            trigger_push_notifications_for_user(push_json, user)
            push_json_admin = {"title": "User Designation Update",
                         "body": f'{user.name} designation has been updated to {user.designation.name} by {current_user.name}.'}
            trigger_push_notifications_for_bb_admins(push_json_admin)

        open_activation = user.activations.filter(UserActivation.date_inactivated == None ).first()
        if open_activation and form.activation.data == 0:
            open_activation.date_inactivated = datetime.now()
            log = ActivityLog(log=f'{current_user.id}-{current_user.name} inactivated user {user.id}-{user.name}',
                              date=datetime.now())
            db.session.add(log)
            db.session.commit()
            open_activation.logs.append(log)
            db.session.commit()

            push_json = {"title": "User Activation Update",
                         "body": f'Your account have been set inactive by {current_user.name}.',
                         }  # "data": {"html": url_for('index')}
            trigger_push_notifications_for_user(push_json, user)
            push_json_admin = {"title": "User Activation Update",
                               "body": f'{user.name}\'s account has been set inactive by {current_user.name}.'}
            trigger_push_notifications_for_bb_admins(push_json_admin)
        elif not open_activation and form.activation.data == 1:
            user_activation = UserActivation(user_id=user.id,
                                         date_activated=datetime.now())
            db.session.add(user_activation)
            db.session.commit()
            log = ActivityLog(log=f'{current_user.id}-{current_user.name} activated user {user.id}-{user.name}',
                              date=datetime.now())
            db.session.add(log)
            db.session.commit()
            user_activation.logs.append(log)
            db.session.commit()
            push_json = {"title": "User Activation Update",
                         "body": f'Your account have been set active by {current_user.name}.',
                         }  # "data": {"html": url_for('index')}
            trigger_push_notifications_for_user(push_json, user)
            push_json_admin = {"title": "User Activation Update",
                               "body": f'{user.name}\'s account has been set active by {current_user.name}.'}
            trigger_push_notifications_for_bb_admins(push_json_admin)
        # # db.session.commit()
        # push_json = {"title": "User Designation Update",
        #              "body": f'Your designation has been updated to {user.designation.name} by {current_user.name}.',
        #              }  # "data": {"html": url_for('index')}
        # trigger_push_notifications_for_user(push_json, user)

        flash(f'{user.name}\'s role/designation has been updated', 'alert-info')
        return redirect(url_for('update_user_role', token=user.get_id_token()))
    elif request.method == 'GET':
        form.designation.data = user.designation_id if user.designation_id else 0
        form.activation.data = 1 if user.is_active() else 0
    return render_template('bulletin_board_admin/update_user_role.html', user=user, form=form, designations=designations,
                           roles=roles, departments=departments)


@app.route('/bulletin_board_admin/add_role_to_user/<user_token>/<role_token>', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def add_role_to_user(user_token, role_token):
    user = User.verify_id_token(user_token)
    role = Role.verify_id_token(role_token)
    if not user or not role:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('bulletin_admin'))
    if not role.is_user_role(user):
        user.roles.append(role)
        log = ActivityLog(log=f'{role.id}-{role.name} added to {user.id}-{user.name} by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        role.logs.append(log)
        user.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": "User Role Update",
                     "body": f'{role.name} role was added to you by {current_user.name}.',
                     }
        trigger_push_notifications_for_user(push_json, user)
        push_json_admin = {"title": "User Role Update",
                           "body": f'{role.name} role was added to {user.name} by {current_user.name}.'}
        trigger_push_notifications_for_bb_admins(push_json_admin)

        flash('Role added', 'alert-info')
    return redirect(url_for('update_user_role', token=user.get_id_token()))


@app.route('/bulletin_board_admin/remove_role_to_user/<user_token>/<role_token>', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def remove_role_to_user(user_token, role_token):
    user = User.verify_id_token(user_token)
    role = Role.verify_id_token(role_token)
    if not user or not role:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('bulletin_admin'))

    if role.is_user_role(user):
        user.roles.remove(role)
        db.session.commit()
        log = ActivityLog(log=f'{role.id}-{role.name} removed from {user.id}-{user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        role.logs.append(log)
        user.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": "User Role Update",
                     "body": f'{role.name} role was removed from you by {current_user.name}.',
                     }
        trigger_push_notifications_for_user(push_json, user)
        push_json_admin = {"title": "User Role Update",
                           "body": f'{role.name} role was removed from {user.name} by {current_user.name}.'}
        trigger_push_notifications_for_bb_admins(push_json_admin)
        flash('Role removed', 'alert-info')
    return redirect(url_for('update_user_role', token=user.get_id_token()))


@app.route('/bulletin_board_admin/add_department_to_user/<user_token>/<department_token>', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def add_department_to_user(user_token, department_token):
    user = User.verify_id_token(user_token)
    department = Department.verify_id_token(department_token)
    if not user or not department:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('bulletin_admin'))
    if not department.is_user_department(user):
        user.departments.append(department)
        log = ActivityLog(log=f'Department {department.id}-{department.name} added to {user.id}-{user.name} by {current_user.id}-{current_user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        department.logs.append(log)
        user.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": "User Department Update",
                     "body": f'{department.name} department was added to you by {current_user.name}.',
                     }
        trigger_push_notifications_for_user(push_json, user)
        push_json_admin = {"title": "User Department Update",
                           "body": f'{department.name} department was added to {user.name} by {current_user.name}.'}
        trigger_push_notifications_for_bb_admins(push_json_admin)

        flash('Department added', 'alert-info')
    return redirect(url_for('update_user_role', token=user.get_id_token()))


@app.route('/bulletin_board_admin/remove_department_to_user/<user_token>/<department_token>', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def remove_department_to_user(user_token, department_token):
    user = User.verify_id_token(user_token)
    department = Department.verify_id_token(department_token)
    if not user or not department:
        flash('Token expired!', 'alert-warning')
        return redirect(url_for('bulletin_admin'))

    if department.is_user_department(user):
        user.departments.remove(department)
        db.session.commit()
        log = ActivityLog(log=f'Department {department.id}-{department.name} removed from {user.id}-{user.name}',
                          date=datetime.now())
        db.session.add(log)
        db.session.commit()
        department.logs.append(log)
        user.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": "User Department Update",
                     "body": f'{department.name} department was removed from you by {current_user.name}.',
                     }
        trigger_push_notifications_for_user(push_json, user)
        push_json_admin = {"title": "User Department Update",
                           "body": f'{department.name} department was removed from {user.name} by {current_user.name}.'}
        trigger_push_notifications_for_bb_admins(push_json_admin)
        flash('Department removed', 'alert-info')
    return redirect(url_for('update_user_role', token=user.get_id_token()))


@app.route('/bulletin_board_admin/submitted_bulletins', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def submitted_bulletins():
    bulletins = Bulletin.query.filter(Bulletin.submitted_date.isnot(None)).filter_by(approve_date=None).all()
    return render_template('bulletin_board_admin/submitted_bulletins.html', bulletins=bulletins)


@app.route('/bulletin_board/publish_bulletin/<token>', methods=['GET', 'POST'])
@login_required
@bb_admin_required
def bulletin_publish_bulletin(token):
    bulletin = Bulletin.verify_id_token(token)
    if not bulletin:
        return redirect(url_for('bulletin_board'))
    if not bulletin.submitted_date:
        return redirect(url_for('bulletin_board'))
    if not bulletin.approve_date:
        bulletin.approved_by_id = current_user.id
        bulletin.approve_date = datetime.now()
        db.session.commit()
        log = ActivityLog(
            log=f'{bulletin.id}-{bulletin.title} published by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        bulletin.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": "Bulletin published",
                     "body": f'Your submitted bulletin {bulletin.title} has been published by {current_user.name}.',
                     }
        trigger_push_notifications_for_user(push_json, bulletin.submitted_by)
        flash('Bulletin published', 'alert-info')
        return redirect(url_for('bulletin_board'))
    elif bulletin.approve_date:
        bulletin.approved_by_id = None
        bulletin.approve_date = None
        db.session.commit()
        log = ActivityLog(
            log=f'{bulletin.id}-{bulletin.title} unpublished by {current_user.id}-{current_user.name}')
        db.session.add(log)
        db.session.commit()
        bulletin.logs.append(log)
        current_user.logs.append(log)
        db.session.commit()
        push_json = {"title": "Bulletin unpublished",
                     "body": f'Your submitted bulletin {bulletin.title} has been unpublished by {current_user.name}.',
                     }
        trigger_push_notifications_for_user(push_json, bulletin.submitted_by)
        flash('Bulletin unpublished', 'alert-info')
        return redirect(url_for('submitted_bulletins'))