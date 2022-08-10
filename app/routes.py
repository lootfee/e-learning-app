import random

from app import app
from flask import render_template, url_for, flash, redirect, request
from app.forms import *
from app.models import *
from app.email import *
from app.web_push_handler import *
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFError
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from time import time as ttime
from datetime import datetime, timedelta, time


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    next = request.referrer
    if current_user.is_authenticated:
        logout_user()
        # flash(f'{e.description}', 'alert-warning')
        # return redirect(url_for('login'))
    flash(f'{e.description}', 'alert-warning')
    return redirect(next)


# to add datetime in jinja templates
@app.context_processor
def inject_datetime_now():
    return {'datetime_now': datetime.now()}


@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js'), 200, {'Content-Type': 'text/javascript', 'Service-Worker-Allowed': '/'}


@app.route('/brand_logo')
def brand_logo():
    return app.send_static_file('brand_logo.png')


@app.route('/brand_icon')
def brand_icon():
    return app.send_static_file('brand_icon.ico')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        two_factor_auth_code = random.randint(10 ** (6 - 1), (10 ** 6) - 1)  # 6 is number of digit to be generated
        token = jwt.encode({
            'data': {'name': reg_form.name.data,
                     'email': reg_form.email.data.lower().replace(' ', ''),
                     'password': reg_form.password.data,
                     'two_factor_auth_code': two_factor_auth_code
                     },
             'exp': ttime() + 600}, #expires in 600 secs
            app.config['SECRET_KEY'], algorithm='HS256')#.decode('utf-8')
        # two_fa = TwoFactorAuthentication(two_fa_code=two_factor_auth_code, token=token, date_created=datetime.now())
        # db.session.add(two_fa)
        # db.session.commit()
        print(datetime.now(), token, two_factor_auth_code)
        send_registration_confirmation_email(reg_form.email.data.lower(), reg_form.name.data, token, two_factor_auth_code)
        flash('Please check your email to confirm your account.', 'alert-info')
        return redirect(url_for('register_user_2fa', token=token))
    return render_template('register.html', reg_form=reg_form)


@app.route('/register_user/two_factor_authentication/<token>', methods=['GET', 'POST'])
def register_user_2fa(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = TwoFactorAuthForm()
    if form.validate_on_submit():
        # two_fa = TwoFactorAuthentication.query.filter_by(two_fa_code=form.code.data, date_used=None).first()
        # if not two_fa:
        #     flash('Invalid code!', 'alert-warning')
        #     return redirect(url_for('update_user_password_2fa'))

        try:
            user_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['data']
        except:
            flash('Invalid token!', 'alert-warning')
            return redirect(url_for('login'))
        if not user_token['two_factor_auth_code'] == form.code.data:
            flash('Invalid token!', 'alert-warning')
            return redirect(url_for('login'))
        user_q = User.query.filter(func.lower(User.email) == user_token['email'].lower()).all()
        if user_q:
            flash('The email is already in use!', 'alert-warning')
            return redirect(url_for('login'))
        user = User(name=user_token['name'],
                    email=user_token['email'])
        user.set_password(user_token['password'])
        db.session.add(user)
        db.session.commit()

        user_pw = UserPassword(user_id=user.id, password_hash=user.password_hash, date_registered=datetime.now())
        db.session.add(user_pw)
        db.session.commit()
        log = ActivityLog(
            log=f'{user.id}-{user.name} email-{user.email} registered')
        db.session.add(log)
        db.session.commit()
        user.logs.append(log)
        db.session.commit()
        body = f'{user.name} registered on the Training and Development app with email {user.email} .'
        email_user(1, 'User registration', body)
        push_json = {"title": "User registration",
                     "body": f'{user.name} registered on the Training and Development app with email {user.email}.'}

        trigger_push_notifications_for_bb_admins(push_json)
        flash("Thank you for registering. You may now be able to log into your account.", 'alert-info')
        return redirect(url_for('login'))
    return render_template('two_factor_auth.html', form=form)


@app.route('/register_user/<token>', methods=['GET', 'POST'])
def register_user(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        user_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['data']
    except:
        flash('Invalid token!', 'alert-warning')
        return redirect(url_for('login'))

    user_q = User.query.filter(func.lower(User.email) == user_token['email'].lower()).all()
    if user_q:
        flash('The email is already in use!', 'alert-warning')
        return redirect(url_for('login'))
    user = User(name=user_token['name'],
                email=user_token['email'])
    user.set_password(user_token['password'])
    db.session.add(user)
    db.session.commit()

    user_pw = UserPassword(user_id=user.id, password_hash=user.password_hash, date_registered=datetime.now())
    db.session.add(user_pw)
    db.session.commit()
    log = ActivityLog(
        log=f'{user.id}-{user.name} email-{user.email} registered')
    db.session.add(log)
    db.session.commit()
    user.logs.append(log)
    db.session.commit()
    body = f'{user.name} registered on the Training and Development app with email {user.email} .'
    email_user(1, 'User registration', body)
    push_json = {"title": "User registration",
                 "body": f'{user.name} registered on the Training and Development app with email {user.email}.'}

    trigger_push_notifications_for_bb_admins(push_json)
    flash("Thank you for registering. You may now be able to log into your account.", 'alert-info')
    return redirect(url_for('login'))


@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if not current_user.is_authenticated: # don't use @login_required decorator
        return redirect(url_for('login')) #password expiry was added to @Login_required so it will cause an infinite loop

    form = UpdatePasswordForm(current_user)
    if form.validate_on_submit():
        two_factor_auth_code = random.randint(10 ** (6 - 1), (10 ** 6) - 1)  # 6 is number of digit to be generated
        token = jwt.encode({
            'data': {'user_id': current_user.id,
                     'name': current_user.name.title(),
                     'email': current_user.email,
                     'password': form.password.data,
                     'two_factor_auth_code': two_factor_auth_code
                     },
            'exp': ttime() + 600},  # expires in 600 secs
            app.config['SECRET_KEY'], algorithm='HS256')#.decode('utf-8')
        # two_fa = TwoFactorAuthentication(two_fa_code=two_factor_auth_code, token=token, date_created=datetime.now())
        # db.session.add(two_fa)
        # db.session.commit()
        print(datetime.now(), token, two_factor_auth_code)
        send_password_update_confirmation_email(current_user.email, current_user.name.title(), token, two_factor_auth_code)
        flash('Please check your email for instructions on how to confirm your account.', 'alert-info')
        return redirect(url_for('update_user_password_2fa', token=token))

    return render_template('update_password.html', title='Update Password', form=form)


@app.route('/update_user_password/two_factor_authentication/<token>', methods=['GET', 'POST'])
def update_user_password_2fa(token):
    if not current_user.is_authenticated:  # don't use @login_required decorator
        return redirect(url_for('login')) #password expiry was added to @Login_required so it will cause an infinite loop
    form = TwoFactorAuthForm()
    if form.validate_on_submit():
        # two_fa = TwoFactorAuthentication.query.filter_by(two_fa_code=form.code.data, date_used=None).first()
        # if not two_fa:
        #     flash('Invalid code!', 'alert-warning')
        #     return redirect(url_for('update_user_password_2fa'))
        try:
            user_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['data']
            # two_fa.date_used = datetime.now()
        except:
            flash('Invalid token!', 'alert-warning')
            return redirect(url_for('login'))

        if current_user.id != int(user_token['user_id']):
            flash('Invalid token!', 'alert-warning')
            return redirect(url_for('login'))

        # user = User.query.get(user_token['user_id'])
        current_user.set_password(user_token['password'])
        db.session.commit()

        user_pw = UserPassword(user_id=current_user.id, password_hash=current_user.password_hash, date_registered=datetime.now())
        db.session.add(user_pw)
        db.session.commit()

        flash("Password updated.", 'alert-info')
        return redirect(url_for('index'))
    return render_template('two_factor_auth.html', form=form)


@app.route('/update_user_password/<token>', methods=['GET', 'POST'])
def update_user_password(token):
    if not current_user.is_authenticated:  # don't use @login_required decorator
        return redirect(url_for('login')) #password expiry was added to @Login_required so it will cause an infinite loop
    try:
        user_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['data']
    except:
        flash('Invalid token!', 'alert-warning')
        return redirect(url_for('login'))

    if current_user.id != int(user_token['user_id']):
        flash('Invalid token!', 'alert-warning')
        return redirect(url_for('login'))

    # user = User.query.get(user_token['user_id'])
    current_user.set_password(user_token['password'])
    db.session.commit()

    user_pw = UserPassword(user_id=current_user.id, password_hash=current_user.password_hash, date_registered=datetime.now())
    db.session.add(user_pw)
    db.session.commit()

    flash("Password updated.", 'alert-info')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    login_form = LoginForm()
    login_form.captcha_token.data = login_form.token
    captcha_img = login_form.captcha_img.data
    if request.method == 'POST':
        ip_address = str(request.access_route[-1])
        lg_attempt = LoginAttempt(email=login_form.email.data, date=datetime.now(), ip_address=ip_address)
        db.session.add(lg_attempt)
        db.session.commit()
        if login_form.validate_on_submit():
            user = User.query.filter(func.lower(User.email) == login_form.email.data.replace(' ', '').lower()).first()
            if user is None or not user.check_password(login_form.password.data):
                lg_attempt.success = False
                lg_attempt.error = 'Invalid email or password'
                db.session.commit()
                flash('Invalid email or password', 'alert-warning')
                return redirect(url_for('login'))
            else:
                if not user.is_active():
                    lg_attempt.success = False
                    lg_attempt.error = 'Account not yet activated'
                    flash('Account not activated. Please inform one of the admins to activate your account.', 'alert-warning')
                    return redirect(url_for('login'))
                else:
                    lg_attempt.success = True
                    # db.session.commit()
                    login_user(user, remember=login_form.remember_me.data)
                    db.session.commit()
                    next_page = request.args.get('next')
                    if not next_page or url_parse(next_page).netloc != '':
                        next_page = url_for('index')
                    return redirect(next_page)
        else:
            lg_attempt.success = False
            lg_attempt.error = 'Invalid form'
            db.session.commit()
            attempts = LoginAttempt.query.filter_by(ip_address=ip_address).order_by(LoginAttempt.date.desc()).all()
            unsuccessful = 0
            for attempt in attempts[:3]:
                if attempt.success == False:
                    unsuccessful += 1
            if unsuccessful == 3:
                return redirect(url_for('login'))
    return render_template('login.html', login_form=login_form, captcha_img=captcha_img)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.email) == form.email.data.lower()).first()
        if user:
            send_password_reset_email(user)
            flash('Check your email for the instructions to reset your password', 'alert-info')
            return redirect(url_for('login'))
        else:
            flash('The email that you entered is not registered on our system.', 'alert-danger')
            return redirect(url_for('reset_password_request'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid token!', 'alert-danger')
        return redirect(url_for('login'))
    form = ResetPasswordForm(user)
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        user_pw = UserPassword(user_id=user.id, password_hash=user.password_hash, date_registered=datetime.now())
        db.session.add(user_pw)
        db.session.commit()

        flash('Your password has been reset.', 'alert-info')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return redirect(url_for('bulletin_board'))


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.email)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data.lower().replace(' ', '')
        db.session.commit()
        log = ActivityLog(
            log=f'{current_user.id}-{current_user.name} {current_user.email} edited profile.')
        db.session.add(log)
        db.session.commit()
        current_user.logs.append(log)
        db.session.commit()
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
    return render_template('edit_profile.html', form=form)




