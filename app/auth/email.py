from flask import render_template, current_app
from app.email import send_email


def admin_send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(('[Stabl] Reset Your Password'),
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/admin_reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/admin_reset_password.html',
                                         user=user, token=token))


def customer_send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(('[Stabl] Reset Your Password'),
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/customer_reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/customer_reset_password.html',
                                         user=user, token=token))
