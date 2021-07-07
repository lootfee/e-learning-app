from app import app, db
from flask import render_template, url_for, flash, redirect, jsonify, request
from flask_login import login_required, login_user, logout_user, current_user
from app.web_push_handler import *

from app.models import PushSubscription


# @app.route("/push-subscriptions", methods=["POST"])
# def create_push_subscription():
#     json_data = request.get_json()
#     subscription = PushSubscription.query.filter_by(
#         subscription_json=json_data['subscription_json'], user_id=current_user.id,
#     ).first()
#     if subscription is None:
#         subscription = PushSubscription(
#             subscription_json=json_data['subscription_json'],
#             user_id=current_user.id
#         )
#         db.session.add(subscription)
#         db.session.commit()
#         print({"result": {
#             "id": subscription.id,
#             "subscription_json": subscription.subscription_json
#         }})
#     else:
#         print('not subscribed')
#     return jsonify({
#         "status": "success",
#         "result": {
#             "id": subscription.id,
#             "subscription_json": subscription.subscription_json,
#             "user_id": subscription.user_id
#         }
#     })
#
#
# #@app.route("/api/trigger-push-notifications", methods=["POST"])
# def trigger_push_notifications_for_all(json):
#     json_data = json# request.get_json()
#     print('trigger_push_notifications', json_data)
#     subscriptions = PushSubscription.query.all()
#     results = trigger_push_notifications_for_all_subscriptions(
#         subscriptions,
#         json_data.get('title'),
#         json_data.get('body'),
#         json_data.get('data')
#     )
#     print('success', results)
#     return jsonify({
#         "status": "success",
#         "result": results
#     })
#
#
# def trigger_push_notifications_for_user(json, user):
#     json_data = json# request.get_json()
#     print('trigger_push_notifications', json_data)
#     results = trigger_push_notifications_for_user_subscriptions(
#         user,
#         json_data.get('title'),
#         json_data.get('body'),
#         json_data.get('data')
#     )
#     print('success', results)
#     return jsonify({
#         "status": "success",
#         "result": results
#     })
#
#
# def trigger_push_notifications_for_user_designation(json, users):
#     json_data = json# request.get_json()
#     print('trigger_push_notifications', json_data)
#     # users = User.query.filter_by(designation_id=user_designation_id).all()
#     results = trigger_push_notifications_for_user_designation_subscriptions(
#         users,
#         json_data.get('title'),
#         json_data.get('body'),
#         json_data.get('data')
#     )
#     print('success', results)
#     return jsonify({
#         "status": "success",
#         "result": results
#     })
