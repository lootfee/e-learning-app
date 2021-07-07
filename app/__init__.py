from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect

import logging
from logging.handlers import SMTPHandler


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Please login to access this page!'
login.login_message_category = 'alert-warning'
mail = Mail(app)
moment = Moment(app)
csrf = CSRFProtect(app)


if not app.debug:
    username = current_user.name if current_user else ''
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr=app.config['ADMINS'][0],#'biogenix-notification@' + app.config['MAIL_SERVER'],
            toaddrs='lutfi.rabago@g42.ai', subject='CME App Failure ' + username,#app.config['ADMINS']
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


from app import web_push_handler, routes, models, forms, cme_routes, cme_admin_routes, cme_forms, cme_models, admin_routes, admin_forms
