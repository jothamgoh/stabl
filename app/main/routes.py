from app.main import bp
from app import db
from flask import render_template, flash, session, redirect, url_for
from app.decorators import login_required
from app.models import Customer, Package, PackageUse
from app.main.forms import SearchCustomerForm, RegisterPackageForm
from app.helperfunc import check_and_clean_phone_number
from flask_login import current_user
from datetime import datetime

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


@bp.route('/package/use-package/<package_id>', methods=['GET', 'POST'])
@login_required(role='customer')
def use_package(package_id):
    p = Package.query.filter_by(cust_id=current_user.id).filter_by(id=package_id).first_or_404()
    num_uses_left = p.package_uses_left_when_keyed - p.package_num_times_used_after_keyed
    if num_uses_left == 1:
        p.is_active = 0
        p.package_num_times_used_after_keyed = p.package_num_times_used_after_keyed + 1
        package_use = PackageUse(package_id=package_id)
        db.session.add(package_use)
        db.session.commit()
        flash('Congrats! You have succesfully used this package. This package is finished and is now inactive.')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    elif num_uses_left <= 0:
        p.is_active = 0
        db.session.commit()
        flash('You have finished using this package.')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    else:
        p.package_num_times_used_after_keyed = p.package_num_times_used_after_keyed + 1
        package_use = PackageUse(package_id=package_id)
        db.session.add(package_use)
        db.session.commit()
        flash('Congrats! You have used this package')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    return render_template('customer_home.html', title='Home')

@bp.route('/package/package-summary/<package_id>', methods=['GET', 'POST'])
@login_required()
def display_package_summary(package_id):
    package = Package.query.filter_by(id=package_id).first_or_404()
    package_data = package.list_customer_package_data()
    
    package_use_list = package.package_usage.order_by(PackageUse.created_at.desc()).all()
    package_use_data = [{'created_at': package_use.created_at} for package_use in package_use_list]
    return render_template('main/package_summary.html', title='Package Summary', package_data=package_data, package_use_data=package_use_data)