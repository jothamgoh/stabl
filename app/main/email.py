from flask import render_template, current_app
from app.email import send_email


def send_package_invoice_email(user):
    send_email(('[Stabl] Invoice for your package'),
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/package_invoice.txt',
                                         user=user),
               html_body=render_template('email/package_invoice.html',
                                         user=user))



# route for sending invoice using email -> to be used in main/routes.py
# @bp.route('/email_package_invoice', methods=['GET', 'POST'])
# @login_required(role='customer')
# def send_package_invoice():
#     send_package_invoice_email(current_user)
#     flash('Package invoice email successfully sent. Please check {}'.format(current_user.email))
#     return render_template('email/package_invoice.html', title='Invoice')
