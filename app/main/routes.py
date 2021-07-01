from app.main import bp
from app import db
from flask import render_template, flash, session, redirect, url_for
from app.decorators import login_required
from app.models import Customer, Package
from app.main.forms import SearchCustomerForm, RegisterPackageForm
from app.helperfunc import check_and_clean_phone_number
from flask_login import current_user

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@bp.route('/admin', methods=['GET', 'POST'])
@bp.route('/admin/index', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_home():
    return render_template('admin_home.html', title='Home')


@bp.route('/home', methods=['GET', 'POST'])
@login_required(role='customer')
def customer_home():
    # list package data
    packages = Package.query.filter_by(cust_id=current_user.id).all()
    package_data = [package.list_customer_package_data() for package in packages]
    return render_template('customer_home.html', title='Home', package_data=package_data)


@bp.route('/admin/search-customer', methods=['GET', 'POST'])
@login_required(role='admin')
def search_for_customer():
    form = SearchCustomerForm()
    if form.validate_on_submit():
        # try to find customer using phone or email
        try:
            phone_number = check_and_clean_phone_number(form.phone_or_email.data)
            customer = Customer.query.filter_by(phone=phone_number).first()
            session['phone_or_email'] = phone_number
            session['cust_id'] = customer.id
        except:
            customer = Customer.query.filter_by(email=form.phone_or_email.data).first()
            session['phone_or_email'] = form.phone_or_email.data
        if customer is None:
            flash(('Customer email or phone not found. Please try again'))
            return redirect(url_for('main.search_for_customer'))
        session['cust_id'] = customer.id 
        return redirect(url_for('main.register_new_package'))
    return render_template('main/search_for_customer.html', title='Find customer', form=form)


@bp.route('/admin/new-package', methods=['GET', 'POST'])
@login_required(role='admin')
def register_new_package():
    form = RegisterPackageForm()
    if form.validate_on_submit():
        new_package = Package(
            admin_id=current_user.get_id(), 
            cust_id=session['cust_id'],
            package_name=form.package_name.data,
            package_total_uses_at_start=form.package_total_uses_at_start.data,
            package_uses_left_when_keyed=form.package_uses_left_when_keyed.data,
            package_price_paid_in_cents=int((form.package_price_paid.data) * 100),
            )
        db.session.add(new_package)
        db.session.commit()
        del session['cust_id']
        flash(('You have created a package for customer with phone/email: {}!'.format(session['phone_or_email'])))
        del session['phone_or_email']
        return redirect(url_for('main.admin_home'))
    return render_template('main/register_new_package.html', title='Key in package details', form=form)

from flask import jsonify

@bp.route('/package/list-package-data', methods=['POST'])
@login_required(role='customer')
def use_package():
    