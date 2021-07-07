from app import app, db
from flask import render_template, url_for, flash, redirect, jsonify, request, current_app
from flask_login import login_required, login_user, logout_user, current_user

from pywebpush import webpush, WebPushException
import json
from threading import Thread

from app.models import PushSubscription


@app.route("/push-subscriptions", methods=["POST"])
def create_push_subscription():
    json_data = request.get_json()
    subscription = PushSubscription.query.filter_by(user_id=current_user.id).first()
    if subscription is None:
        subscription = PushSubscription(
            subscription_json=json_data['subscription_json'],
            user_id=current_user.id
        )
        db.session.add(subscription)
        db.session.commit()
        print({"result": {
            "id": subscription.id,
            "subscription_json": subscription.subscription_json
        }})
    else:
        subscription.subscription_json = json_data['subscription_json']
        db.session.commit()
    return jsonify({
        "status": "success",
        "result": {
            "id": subscription.id,
            "subscription_json": subscription.subscription_json,
            "user_id": subscription.user_id
        }
    })


#@app.route("/api/trigger-push-notifications", methods=["POST"])
def trigger_push_notifications_for_all(json):
    json_data = json# request.get_json()
    print('trigger_push_notifications', json_data)
    subscriptions = PushSubscription.query.all()
    title = json_data.get('title')
    body = json_data.get('body')
    data = json_data.get('data')
    # results = trigger_push_notifications_for_all_subscriptions(
    #     subscriptions,
    #     json_data.get('title'),
    #     json_data.get('body'),
    #     json_data.get('data')
    # )
    Thread(target=trigger_push_notifications_for_all_subscriptions, args=(subscriptions, title, body, data)).start()
    # print('success', results)
    # return jsonify({
    #     "status": "success",
    #     "result": results
    # })


def trigger_push_notifications_for_user(json, user):
    json_data = json# request.get_json()
    print('trigger_push_notifications', json_data)
    title = json_data.get('title')
    body = json_data.get('body')
    data = json_data.get('data')
    # results = trigger_push_notifications_for_user_subscriptions(
    #     user,
    #     json_data.get('title'),
    #     json_data.get('body'),
    #     json_data.get('data')
    # )
    Thread(target=trigger_push_notifications_for_user_subscriptions, args=(user, title, body, data)).start()
    # print('success', results)
    # return jsonify({
    #     "status": "success",
    #     "result": results
    # })


def trigger_push_notifications_for_user_designation(json, users):
    json_data = json
    print('trigger_push_notifications', json_data)
    # users = User.query.filter_by(designation_id=user_designation_id).all()
    title = json_data.get('title')
    body = json_data.get('body')
    data = json_data.get('data')
    # results = trigger_push_notifications_for_user_designation_subscriptions(
    #     users,
    #     json_data.get('title'),
    #     json_data.get('body'),
    #     json_data.get('data')
    # )
    Thread(target=trigger_push_notifications_for_user_designation_subscriptions, args=(users, title, body, data)).start()
    # print('success', results)
    # return jsonify({
    #     "status": "success",
    #     "result": results
    # })


def trigger_push_notification(push_subscription, title, body, data):
    try:
        response = webpush(
            subscription_info=json.loads(push_subscription.subscription_json),
            data=json.dumps({"title": title, "body": body, "data": data}),
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims={
                "sub": "mailto:{}".format(
                    current_app.config["VAPID_CLAIM_EMAIL"])
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
                "Accept-Encoding": "*",
                "Connection": "keep-alive",
                'Content-Type': 'application/json'
            }
        )

        return response.ok

    except WebPushException as ex:
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}",
                  extra.code,
                  extra.errno,
                  extra.message
                  )
        return False


def trigger_push_notifications_for_all_subscriptions(subscriptions, title, body, data):
    with app.app_context():
        return [trigger_push_notification(subscription, title, body, data)
                for subscription in subscriptions]


def trigger_push_notifications_for_user_subscriptions(user, title, body, data):
    return [
        trigger_push_notification(subscription, title, body, data)
        for subscription in user.push_subscriptions]


def trigger_push_notifications_for_user_designation_subscriptions(users, title, body, data):
    with app.app_context():
        return {user.id: trigger_push_notifications_for_user_subscriptions(user, title, body) for user in users}