from flask import render_template, redirect, url_for, flash, request, session
from twilio.rest import TwilioTaskRouterClient
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app import db
from app.models import Customer, User, Admin
from app.auth.forms import AdminLoginForm, AdminRegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, CustomerLoginOTPForm, CustomerRegistrationForm, CustomerOTPForm, CustomerLoginForm, InputEmailAndPasswordForm
from app.auth.email import admin_send_password_reset_email, customer_send_password_reset_email
from app.decorators import login_required
from app.auth.twilio_verify import request_verification_token, check_verification_token
from app.helperfunc import check_and_clean_phone_number, invalid_phone_number_message


@bp.route('/login/admin', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_home'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(('Invalid username or password'), 'danger')
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
        user = Admin(name=form.name.data, email=form.email.data, company_id=current_user.company_id)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(('Congratulations, {} is now a registered admin!'.format(user.email)), 'success')
        return redirect(url_for('auth.admin_login'))
    return render_template('auth/admin_register.html', title=('Admin Register'),
                           form=form)


@bp.route('/login', methods=['GET', 'POST'])
def customer_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    form = CustomerLoginForm()
    if form.validate_on_submit():
        try:
            phone_number = check_and_clean_phone_number(form.phone_or_email.data)
            user = Customer.query.filter_by(phone=phone_number).first()
        except:
            user = Customer.query.filter_by(email=form.phone_or_email.data).first()
        try:
            if user is None or not user.check_password(form.password.data): # check password returns an error if password is not set. Hence try except block added in
                flash(('Invalid email, phone number or password'), 'danger')
                return redirect(url_for('auth.customer_login'))
        except:
            flash(('Your password is not set. Login using your phone number and OTP instead.'), 'danger')
            return redirect(url_for('auth.customer_login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.customer_home')
        return redirect(next_page)
    return render_template('auth/customer_login.html', title=('Sign In'), form=form)


@bp.route('/login-otp', methods=['GET', 'POST'])
def customer_login_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    form = CustomerLoginOTPForm()
    if form.validate_on_submit():
        try:
            phone_number = check_and_clean_phone_number(form.phone.data)
        except:
            flash (invalid_phone_number_message(), 'danger')
            return redirect(url_for('auth.customer_login_otp'))
        user = Customer.query.filter_by(phone=phone_number).first()
        if user is None:
            flash(('Invalid phone number'), 'danger')
            return redirect(url_for('auth.customer_login_otp'))
        request_verification_token(phone_number)
        session['phone'] = phone_number  
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.customer_home')
        return redirect(url_for('auth.customer_otp', next=next_page, remember='1' if form.remember_me.data else '0'))
    return render_template('auth/customer_login_otp.html', title=('Sign In'), form=form)


@bp.route('/login-otp-validation', methods=['GET', 'POST'])
def customer_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    form = CustomerOTPForm()
    if form.validate_on_submit():
        phone = session['phone']
        token = form.otp.data
        if check_verification_token(phone, token):
            user = Customer.query.filter_by(phone=phone).first()
            remember = request.args.get('remember', '0') == '1'
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if user.email is None and user.password_hash is None:
                return redirect(url_for('auth.set_email_and_password')) 
            del session['phone']
            try:
                return redirect(next_page)
            except:
                return redirect(url_for('main.customer_home')) # if customer keys in wrong OTP first time round, error. This is the fallback
        else:
            flash(('Invalid OTP. Please key in again'), 'danger')
            return redirect(url_for('auth.customer_otp'))
    return render_template('auth/customer_otp.html', title=('Key in One Time Password'), form=form)


@bp.route('/set-email-and-password', methods=['GET', 'POST'])
@login_required(role='customer')
def set_email_and_password():
    form = InputEmailAndPasswordForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.set_password(form.password.data)
        db.session.commit()
        return redirect(url_for('main.customer_home'))
    elif request.method == 'GET':
        form.name.data = current_user.name
    return render_template('auth/set_email_and_password.html', title=('Confirm email and password'), form=form)



@bp.route('/register-customer', methods=['GET', 'POST'])
@login_required(role='admin')
def customer_register():
    form = CustomerRegistrationForm()
    if form.validate_on_submit():
        try:
            phone_number = check_and_clean_phone_number(form.phone.data)
        except:
            flash (invalid_phone_number_message(), 'danger')
            return redirect(url_for('auth.customer_register'))
        user = Customer(name=form.name.data, email=form.email.data, phone=phone_number)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(('Congratulations, {} is now a registered customer! Please ask them to log in'.format(user.phone)), 'success')
        return redirect(url_for('main.admin_home'))
    return render_template('auth/customer_register.html', title=('Register Customer'),
                           form=form)


@bp.route('/admin_reset_password_request', methods=['GET', 'POST'])
def admin_reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user:
            admin_send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'success')
        return redirect(url_for('auth.admin_login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/admin_reset_password/<token>', methods=['GET', 'POST'])
def admin_reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_home'))
    user = Admin.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.admin_login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/customer_reset_password_request', methods=['GET', 'POST'])
def customer_reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Customer.query.filter_by(email=form.email.data).first()
        if user:
            customer_send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'success')
        return redirect(url_for('auth.customer_login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/customer_reset_password/<token>', methods=['GET', 'POST'])
def customer_reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.customer_home'))
    user = Customer.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.customer_login'))
    return render_template('auth/reset_password.html', form=form)