from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app import db
from app.models import Customer, User, Admin
from app.auth.forms import AdminLoginForm, AdminRegistrationForm, AdminResetPasswordRequestForm, AdminResetPasswordForm, CustomerLoginForm, CustomerRegistrationForm, CustomerOTPForm
from app.auth.email import send_password_reset_email
from app.decorators import login_required
from app.auth.twilio_verify import request_verification_token, check_verification_token, check_and_clean_phone_number

@bp.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_home'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(('Invalid username or password'))
            return redirect(url_for('auth.admin_login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.admin_home')
        return redirect(next_page)
    return render_template('auth/admin_login.html', title=('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/admin/register', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_register():
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        user = Admin(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(('Congratulations, {} is now a registered admin!'.format(user.email)))
        return redirect(url_for('auth.admin_login'))
    return render_template('auth/admin_register.html', title=('Register'),
                           form=form)


@bp.route('/reset-password-request', methods=['GET', 'POST'])
def admin_reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_home'))
    form = AdminResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
        ('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def customer_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    form = CustomerLoginForm()
    if form.validate_on_submit():
        phone_number = check_and_clean_phone_number(form.phone.data)
        user = Customer.query.filter_by(phone=phone_number).first()
        if user is None or not user.check_phone(phone_number):
            flash(('Invalid phone number'))
            return redirect(url_for('auth.customer_login'))
        request_verification_token(phone_number)
        session['phone'] = check_and_clean_phone_number(phone_number)  
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.customer_home')
        return redirect(url_for('auth.customer_otp', next=next_page, remember='1' if form.remember_me.data else '0'))
    return render_template('auth/customer_login.html', title=('Sign In'), form=form)


@bp.route('/login-otp', methods=['GET', 'POST'])
def customer_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    form = CustomerOTPForm()
    if form.validate_on_submit():
        phone = check_and_clean_phone_number(session['phone'])
        token = form.otp.data
        if check_verification_token(phone, token):
            user = Customer.query.filter_by(phone=phone).first()
            next_page = request.args.get('next')
            remember = request.args.get('remember', '0') == '1'
            login_user(user, remember=remember)
            return redirect(next_page)
        else:
            print('error why is this happening', file=sys.stderr)
            flash(('Invalid OTP. Please key in again'))
            return redirect(url_for('auth.customer_otp'))
    return render_template('auth/customer_otp.html', title=('Key in One Time Password'), form=form)


@bp.route('/register-customer', methods=['GET', 'POST'])
@login_required(role='admin')
def customer_register():
    form = CustomerRegistrationForm()
    if form.validate_on_submit():
        user = Customer(name=form.name.data, email=form.email.data, phone=check_and_clean_phone_number(form.phone.data))
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(('Congratulations, {} is now a registered customer! Please ask them to log in'.format(user.phone)))
        return redirect(url_for('main.admin_home'))
    return render_template('auth/customer_register.html', title=('Register'),
                           form=form)