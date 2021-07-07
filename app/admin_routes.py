from app import app
from flask import render_template, url_for, flash, redirect, request
from app.admin_forms import *
from app.models import *
from app.email import *
from app.service_worker import *
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from time import time as ttime
from datetime import datetime, timedelta, time


@app.route('/designation', methods=['GET', 'POST'])
@login_required
def designation():
    if current_user.id != 1:
        redirect(url_for('index'))
    designations = Designation.query.all()
    form = AddDesignationForm()
    if form.validate_on_submit():
        designation = Designation(name=form.name.data)
        db.session.add(designation)
        db.session.commit()
        return redirect(url_for('designation'))
    return render_template('cme_admin/designation.html', designations=designations, form=form)


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if current_user.id != 1 or current_user.designation_id > 2 if current_user.designation_id else None:
        return redirect(url_for('index'))
    users = User.query.order_by(User.name.asc()).all()
    designations = Designation.query.order_by(Designation.name.asc()).all()
    form = AddUserForm()
    form.designation.choices = [(0, 'Select Designation')] + [(d.id, d.name) for d in designations]
    if form.submit.data:
        if form.validate_on_submit():
            new_user = User(name=form.name.data,
                            email=form.email.data.lower().replace(' ', ''),
                            designation_id=form.designation.data)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('users'))
    edit_designation_form = EditUserDesignationForm()
    edit_designation_form.ed_designation.choices = [(0, 'Select Designation')] + [(d.id, d.name) for d in designations]
    if edit_designation_form.ed_submit.data:
        if edit_designation_form.validate_on_submit():
            edit_user = User.verify_id_token(edit_designation_form.ed_user_id.data)
            if edit_user:
                edit_user.designation_id = edit_designation_form.ed_designation.data
                db.session.commit()
                push_json = {"title": "User Designation Update",
                             "body": f'Your designation has been updated to {edit_user.designation.name} by {current_user.name}.',
                             } #"data": {"html": url_for('index')}
                trigger_push_notifications_for_user(push_json, edit_user)

                flash(f'{edit_user.name}\'s designation has been updated', 'alert-info')
            else:
                flash('Cannot find user.', 'alert-warning')
            return redirect(url_for('users'))
    return render_template('cme_admin/users.html', users=users, form=form, edit_designation_form=edit_designation_form)



@app.route('/nursing_admin', methods=['GET', 'POST'])
@login_required
def nursing_admin():
    if current_user.id == 1 or current_user.designation_id <= 2 if current_user.designation_id else None:
        users = User.query.all()
        designations = Designation.query.all()
        return render_template('nursing_admin/admin_index.html', users=users, designations=designations)
    else:
        redirect(url_for('index'))
