#!/bin/dash
. venv/bin/activate
flask db init
flask db migrate
flask db upgrade
export FLASK_DEBUG=1
exec gunicorn --timeout 1000 --workers 1 --threads 4 -b :5000 --access-logfile - --error-logfile - main:app
#source venv/bin/activate
#flask db init
#flask db migrate
#flask db upgrade
#
#exec gunicorn -b :5000 --access-logfile - --error-logfile - main:app