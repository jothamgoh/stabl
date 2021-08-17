from app.auth.forms import ResetPasswordForm
from re import search
from app.main import bp
from app import db
from flask import render_template, flash, session, redirect, url_for, request
from app.decorators import login_required
from app.models import Company, Customer, Package, PackageUse, User, Admin, CompanyPackagesAndProducts, CustomerOrders, Outlet
from app.main.forms import CreateProductOrderForm, RegisterPackageForm, PortCustomerAndPackageForm, TransferPackageForm, SearchCustomerForm, AddCompanyItemForm, CreateProductOrderForm,\
UpdateCustomerSettingsForm, UpdateAdminSettingsForm, UpdateAdminOutletForm, AddNewOutletForm
from app.helperfunc import check_and_clean_phone_number, invalid_phone_number_message, check_if_cust_exists_else_create_return_custid
from flask_login import current_user
from app.main.email import send_package_invoice_email # to be enabled once in production
from sqlalchemy.sql.expression import func


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@bp.route('/admin', methods=['GET', 'POST'])
@bp.route('/admin/index', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_home():
    admins_obj = Admin.query.filter_by(company_id=current_user.company_id).all()
    admin_data = [admin.list_admin_data() for admin in admins_obj]
    return render_template('admin_home.html', title='Admin Dashboard', admin_data=admin_data)


@bp.route('/admin/deactivate/<admin_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def deactivate_admin(admin_id):
    a = Admin.query.filter_by(company_id=current_user.company_id).filter_by(id=admin_id).first()
    admin_name = a.name
    a.is_active = 0
    db.session.commit()
    flash(('Your have deactivated admin: {}.'.format(admin_name)), 'danger')
    return redirect(url_for('main.admin_home'))


@bp.route('/admin/activate/<admin_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def activate_admin(admin_id):
    a = Admin.query.filter_by(company_id=current_user.company_id).filter_by(id=admin_id).first()
    admin_name = a.name
    a.is_active = 1
    db.session.commit()
    flash(('Your have activated admin: {}.'.format(admin_name)), 'success')
    return redirect(url_for('main.admin_home'))


@bp.route('/home', methods=['GET', 'POST'])
@login_required(role='customer')
def customer_home():
    # list package data
    packages = Package.query.filter_by(cust_id=current_user.id).all()
    package_data = [package.list_customer_package_data() for package in packages]
    return render_template('customer_home.html', title='Home', package_data=package_data)

@bp.route('/admin/search-customer', methods=['GET', 'POST'])
@login_required(role='admin')
def search_for_customer(): # this does not filter customer by company. This filters every customer in the database with Stabl
    company_id = current_user.company_id
    form = SearchCustomerForm()
    if form.validate_on_submit():
        # try to find customer using phone or email
        try: # case when customer keys in phone number
            phone_number = check_and_clean_phone_number(form.phone_or_email.data) # if email, exception is raised. if phone number is invalid 'None' returned
            customer = Customer.query.filter_by(phone=phone_number).first()
        except: # case when customer keys in email or if phone number is invalid
            customer = Customer.query.filter_by(email=form.phone_or_email.data).first()
        if customer is None :
            flash(('Customer email or phone not found. Please try again'), 'danger')
            del session['cust_id']
            return redirect(url_for('main.search_for_customer'))
        count_num_packages = Package.query.filter_by(company_id=company_id).filter_by(cust_id=customer.id).count()
        if count_num_packages == 0: # if customer exists, but does not have any packages with the salon
            flash(('Customer does not have any existing packages with your company.'), 'danger')
            del session['cust_id']
            return redirect(url_for('main.search_for_customer'))
        session['cust_id'] = customer.id 
        return redirect(url_for('main.customer_home_admin_view', cust_id=session['cust_id']))
    return render_template('main/search_for_customer.html', title='Find customer', form=form)


@bp.route('/admin/customer-home/<cust_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def customer_home_admin_view(cust_id):
    # list package data
    packages = Package.query.filter_by(company_id=current_user.company_id).filter_by(cust_id=session['cust_id']).all()
    package_data = [package.list_customer_package_data() for package in packages]
    return render_template('customer_home.html', title='Home', package_data=package_data)


@bp.route('/admin/new-package', methods=['GET', 'POST'])
@login_required(role='admin')
def register_new_package():
    form = RegisterPackageForm()
    company_id = current_user.company_id
    # populate package_choices
    company_packages_obj = CompanyPackagesAndProducts.query.filter_by(company_id=company_id).filter_by(item_type='service').all()
    form.package_name.choices = [(p.item_name) for p in company_packages_obj]
    if form.validate_on_submit():
        if current_user.outlet_id is None:
            flash(('Package not registered! Please tag your account to a store before trying again.'), 'danger')
            return redirect(url_for('main.port_customer_and_package'))
        phone_number = check_and_clean_phone_number(form.phone.data)
        cust_id = check_if_cust_exists_else_create_return_custid(phone=phone_number)
        package_num_total_uses_at_start = form.package_num_total_uses_at_start.data
        package_num_used_when_keyed = form.package_num_used_when_keyed.data
        package_price_paid_in_cents = int((form.package_price_paid.data) * 100)
        company_id = company_id

        if package_num_total_uses_at_start <= package_num_used_when_keyed or package_price_paid_in_cents < 0:
            flash(('The data you entered does not make sense. Please check and try again.', 'danger'))
            return redirect(url_for('main.register_new_package'))
        new_package = Package(
            admin_id=current_user.get_id(),
            outlet_id=current_user.outlet_id,
            outlet_name=current_user.outlet_name, 
            cust_id=cust_id,
            company_id=company_id,
            package_name=form.package_name.data,
            package_num_total_uses_at_start=package_num_total_uses_at_start,
            package_num_used_when_keyed=package_num_used_when_keyed,
            package_price_paid_in_cents=package_price_paid_in_cents
            )
        db.session.add(new_package)
        db.session.commit()
        flash(('You have created a package for customer with phone number: {}'.format(phone_number)), 'success')
        # send_package_invoice_email(current_user)
        return redirect(url_for('main.admin_home'))
    return render_template('main/register_new_package.html', title='Key in package details', form=form)


@bp.route('/package/use-package/<package_id>', methods=['GET', 'POST'])
@login_required()
def use_package(package_id):
    package_user_id = current_user.id
    package_user_role = User.query.filter_by(id=package_user_id).first().role

    p = Package.query.filter_by(id=package_id).first_or_404()

    num_uses_left = p.num_uses_left()
    if num_uses_left <= 0:
        p.is_active = 0
        db.session.commit()
        flash('You have finished using this package.', 'danger')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    else:
        if num_uses_left == 1:
            p.is_active = 0
        p.package_num_times_used_after_keyed = p.package_num_times_used_after_keyed + 1
        # insert package use data
        package_use = PackageUse(package_id=package_id)
        package_use.num_uses = 1 # number times package used is 1 time
        if package_user_role == 'admin': # if admin use package, take down the name of the admin
            admin_name = Admin.query.filter_by(id=package_user_id).first().name
            package_use.who_used_package = 'Staff ({})'.format(admin_name)
        else: # else, it's the self who use package
            package_use.who_used_package = 'self'
        db.session.add(package_use)
        db.session.commit()
        flash('Congrats! You have used this package', 'success')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    return render_template('customer_home.html', title='Home')


@bp.route('/package/package-summary/<package_id>', methods=['GET', 'POST'])
@login_required()
def display_package_summary(package_id):
    package = Package.query.filter_by(id=package_id).first_or_404()
    package_data = package.list_customer_package_data()
    
    package_use_list = package.package_usage.order_by(PackageUse.created_at.desc()).all()
    package_use_data = [package_use.list_package_use_data() for package_use in package_use_list]

    return render_template('main/package_summary.html', title='Package Summary', package_data=package_data, package_use_data=package_use_data)


@bp.route('/package/transfer-package/<package_id>', methods=['GET', 'POST'])
@login_required(role='customer')
def transfer_package(package_id):
    current_cust_id = current_user.id
    p = Package.query.filter_by(cust_id=current_cust_id).filter_by(id=package_id).first_or_404() # p is the original package in question
    package_data = p.list_customer_package_data()
    num_uses_left = p.num_uses_left()
    form = TransferPackageForm()
    if form.validate_on_submit():
        phone_number = check_and_clean_phone_number(form.phone.data)
        if phone_number == current_user.phone:
            flash('You cannot transfer a package to your own phone number.', 'danger')
            return redirect(url_for('main.transfer_package', package_id=package_id))
        num_uses_to_transfer = form.num_uses_to_transfer.data
        if num_uses_left < num_uses_to_transfer: # not possible, redirect to same page
            flash('You cannot transfer more uses than what you have. Please try again', 'danger')
            return redirect(url_for('main.transfer_package', package_id=package_id))
        else: 
            if num_uses_left==num_uses_to_transfer:
                p.is_active = 0
            p.package_num_times_transferred += num_uses_to_transfer
            new_cust_id = check_if_cust_exists_else_create_return_custid(phone=phone_number)
            new_package_for_transferee = Package(
                admin_id=None,
                cust_id=new_cust_id,
                outlet_id=package_data['outlet_id'],
                outlet_name=package_data['outlet_name'],
                company_id=p.company_id,
                package_name=p.package_name,
                package_num_total_uses_at_start=num_uses_to_transfer,
                package_price_paid_in_cents=0,
                is_transferred=1,
                transferred_from_package_id=package_id
            )
            db.session.add(new_package_for_transferee)
            db.session.commit()

            # PackageUse data
            # The person transferring the package
            p_transferor = PackageUse(package_id=package_id)
            p_transferor.who_used_package = phone_number # phone number of the person i am transferring to
            p_transferor.num_uses = num_uses_to_transfer
            p_transferor.is_package_transfer = 1
            db.session.add(p_transferor)

            # The person reciving the package
            p_recipient = PackageUse(package_id=new_package_for_transferee.id)
            p_recipient.who_used_package = current_user.phone # phone of the person I received the package from
            p_recipient.num_uses = -num_uses_to_transfer
            p_recipient.is_package_transfer = 1
            db.session.add(p_recipient)
            db.session.commit()            

            flash('You have transferred {} package/s to phone number: {}'.format(num_uses_to_transfer, phone_number), 'success')
            return redirect(url_for('main.customer_home'))
    return render_template('main/transfer_package.html', title='Transfer package to a friend', form=form, package_data=package_data) 


@bp.route('/admin/port-package', methods=['GET', 'POST'])
@login_required(role='admin')
def port_customer_and_package():
    form = PortCustomerAndPackageForm()
    # populate package_choices
    company_id = current_user.company_id
    company_packages_obj = CompanyPackagesAndProducts.query.filter_by(company_id=company_id).filter_by(item_type='service').all()
    form.package_name.choices = [(p.item_name) for p in company_packages_obj]
    if form.validate_on_submit():
        if current_user.outlet_id is None:
            flash(('Package not ported over! Please tag your account to a store before trying again.'), 'danger')
            return redirect(url_for('main.port_customer_and_package'))
        phone_number = check_and_clean_phone_number(form.phone.data)
        cust_id = check_if_cust_exists_else_create_return_custid(phone=phone_number, name=form.name.data)
        new_package  = Package(
            admin_id=current_user.get_id(),
            cust_id=cust_id,
            outlet_id=current_user.outlet_id,
            outlet_name=current_user.outlet_name,
            company_id=current_user.company_id,
            package_name=form.package_name.data,
            package_num_total_uses_at_start=form.package_num_total_uses_at_start.data,
            package_num_used_when_keyed=form.package_num_used_when_keyed.data,
            package_price_paid_in_cents=int((form.package_price_paid.data) * 100),
            created_at=form.created_at.data,
            is_ported_over = 1
        )
        db.session.add(new_package)
        db.session.commit()

        package_id=new_package.id
        flash('Package successfully ported over. Please confirm details are correct.', 'success')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    return render_template('main/port_customer_and_package.html', title='Port package', form=form)


@bp.route('/package-invoice/<package_id>', methods=['GET'])
@login_required(role='customer')
def display_package_invoice(package_id):
    p = Package.query.filter_by(cust_id=current_user.id).filter_by(id=package_id).first_or_404()
    package_data = p.list_customer_package_data()
    return render_template('main/package_invoice.html', title='Invoice', package_data=package_data)


# display company services or products
@bp.route('/admin/display_items/<service_or_product>', methods=['GET', 'POST'])
@login_required(role='admin')
def display_items(service_or_product): # this route includes adding new services and products to a company
    # data to render page
    service_or_product = service_or_product
    company_id = current_user.company_id
    company_items = CompanyPackagesAndProducts.query.filter_by(company_id=company_id).filter_by(item_type=service_or_product).all()
    company_item_data = [item.list_item_attributes() for item in company_items]

    # form data for register package modal
    form = AddCompanyItemForm()
    if form.validate_on_submit():
        item_price_in_cents = int((form.item_price.data) * 100)
        new_item = CompanyPackagesAndProducts(
            company_id=company_id, 
            item_name=form.item_name.data,
            item_price_in_cents=item_price_in_cents,
            item_type = service_or_product
            )
        db.session.add(new_item)
        db.session.commit()
        flash(('New {} "{}" added and can now be used.'.format(service_or_product, form.item_name.data)), 'success')
        return redirect(url_for('main.display_items', service_or_product=service_or_product))
    return render_template('main/display_company_items.html', title='Display {}'.format(service_or_product), company_item_data=company_item_data, form=form, service_or_product=service_or_product)


@bp.route('/admin/edit_item/<item_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_existing_item(item_id):
    form = AddCompanyItemForm()
    package_obj = CompanyPackagesAndProducts.query.filter_by(company_id=current_user.company_id).filter_by(id=item_id).first()
    package_data_dict = package_obj.list_item_attributes()
    if form.validate_on_submit():
        item_price_in_cents = int((form.item_price.data) * 100)
        package_obj.item_name = form.item_name.data 
        package_obj.item_price_in_cents = item_price_in_cents
        db.session.commit()
        flash(('Successfully edited item: {}'.format(form.item_name.data)), 'success')
        return redirect(url_for('main.display_items', service_or_product=package_data_dict['item_type'])) 
    elif request.method == 'GET':
        form.item_name.data = package_data_dict['item_name']
        form.item_price.data = package_data_dict['item_price_in_cents'] / 100
    return render_template('main/edit_existing_item.html', title='Edit Item', form=form, package_data_dict=package_data_dict)


@bp.route('/admin/delete_item/<item_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def delete_existing_item(item_id):
    package_obj = CompanyPackagesAndProducts.query.filter_by(company_id=current_user.company_id).filter_by(id=item_id).first()
    package_data_dict = package_obj.list_item_attributes()
    service_or_product = package_data_dict['item_type']
    item = CompanyPackagesAndProducts.query.filter_by(company_id=current_user.company_id).filter_by(id=item_id).first()
    db.session.delete(item)
    db.session.commit()
    flash(('Successfully deleted item: {}'.format(package_data_dict['item_name'])), 'success')
    return redirect(url_for('main.display_items', service_or_product=service_or_product))


@bp.route('/admin/create-new-item', methods=['GET', 'POST'])
@login_required(role='admin')
def add_item_to_cart():
    # data to render page
    company_id = current_user.company_id
    form = CreateProductOrderForm()
    # populate package_choices
    company_packages_obj = Company.query.filter_by(id=company_id).first().company_packages_and_products.all()
    package_names = [(p.item_name) for p in company_packages_obj]
    form.item_name.choices = package_names

    d = {}
    if form.validate_on_submit():
        price_per_item_in_cents = int((form.item_price.data) * 100)
        item_discount = int((form.item_discount.data) * 100)
        d['company_id'] = company_id
        d['admin_id'] = current_user.id
        d['item_name'] = form.item_name.data
        d['package_or_product_id'] = CompanyPackagesAndProducts.query.filter_by(company_id=current_user.company_id).filter_by(item_name=form.item_name.data).first().id
        d['price_per_item_in_cents'] = price_per_item_in_cents
        d['discount_per_item_in_cents'] = item_discount
        d['quantity'] = form.item_quantity.data
        if 'checkout' not in session:
            session['checkout'] = [d]
        else: 
            cart_list = session['checkout']
            cart_list.append(d)
            session['checkout'] = cart_list  # 
    return render_template('main/checkout.html', title="Checkout", form=form)


@bp.route('/admin/clear-cart', methods=['GET', 'POST'])
@login_required(role='admin')
def clear_cart():
    session.pop('checkout', None)
    return redirect(url_for('main.add_item_to_cart'))


@bp.route('/admin/checkout', methods=['GET', 'POST'])
@login_required(role='admin')
def checkout():
    if current_user.outlet_id is None:
        flash(('Order not submitted! Please tag your account to a store before trying again.'), 'danger')
        return redirect(url_for('main.add_item_to_cart'))
    checkout_data = session['checkout']
    max_id = db.session.query(func.max(CustomerOrders.id)).filter_by(company_id=1).first()[0]
    if max_id is None:
        order_number = 1
    else:
        order_number = max_id + 1
    for d in checkout_data:
        new_item = CustomerOrders(
            order_number = order_number,
            company_id=d['company_id'],
            outlet_id=current_user.outlet_id,
            outlet_name=current_user.outlet_name, 
            admin_id=d['admin_id'],
            package_or_product_id=d['package_or_product_id'],
            item_name = d['item_name'],
            price_per_item_in_cents=d['price_per_item_in_cents'],
            discount_per_item_in_cents=d['discount_per_item_in_cents'],
            quantity=d['quantity'],
            status='completed'
            )
        db.session.add(new_item)
    db.session.commit()
    del session['checkout']
    flash(('Order successful! Please make sure you have collected payment.'), 'success')
    return render_template('main/checkout_summary.html', title="Checkout Summary", checkout_data=checkout_data, order_number=order_number)
    

@bp.route('/admin/add-outlet', methods=['GET', 'POST'])
@login_required(role='admin')
def add_new_outlet(): # this route includes displaying all outlets of a company
    form = AddNewOutletForm()
    company_id = current_user.company_id
    outlets_obj = Outlet.query.filter_by(company_id=company_id).all()
    outlets_data = [outlet.list_outlet_attributes() for outlet in outlets_obj]
    if form.validate_on_submit():
        try:
            phone_number = check_and_clean_phone_number(form.phone.data)
        except:
            flash(invalid_phone_number_message(), 'danger')
            return redirect(url_for('main.add_new_outlet'))
        new_outlet = Outlet(
            company_id=company_id,
            outlet_name = form.outlet_name.data, 
            postal = form.postal.data,
            unit_number = form.unit_number.data,
            address = form.address.data,
            phone = phone_number,
            email = form.email.data
            )
        db.session.add(new_outlet)
        db.session.commit()
        flash('You succesfully created a new outlet: {}'.format(form.outlet_name.data), 'success')
        return redirect(url_for('main.add_new_outlet'))
    return render_template('main/add_new_outlet.html', title='Add New Outlet', form=form, outlets_data=outlets_data)


@bp.route('/admin/edit-outlet-data/<outlet_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_outlet_data(outlet_id):
    form = AddNewOutletForm()
    company_id = current_user.company_id
    outlet_obj = Outlet.query.filter_by(company_id=company_id).filter_by(id=outlet_id).first()
    outlet_data_dict = outlet_obj.list_outlet_attributes()
    if form.validate_on_submit():
        try:
            phone_number = check_and_clean_phone_number(form.phone.data)
        except:
            flash(invalid_phone_number_message(), 'danger')
            return redirect(url_for('main.add_new_outlet'))
        outlet_obj.outlet_name = form.outlet_name.data 
        outlet_obj.postal = form.postal.data 
        outlet_obj.unit_number = form.unit_number.data 
        outlet_obj.address = form.address.data 
        outlet_obj.email = form.email.data 
        outlet_obj.phone = phone_number 
        db.session.commit()
        flash(('Successfully edited outlet: {}'.format(form.outlet_name.data)), 'success')
        return redirect(url_for('main.add_new_outlet')) 
    elif request.method == 'GET':
        form.outlet_name.data = outlet_data_dict['outlet_name']
        form.postal.data = outlet_data_dict['postal']
        form.unit_number.data = outlet_data_dict['unit_number']
        form.address.data = outlet_data_dict['address']
        form.phone.data = outlet_data_dict['phone']
        form.email.data = outlet_data_dict['email']
    return render_template('main/edit_outlet_data.html', title='Edit Outlet', form=form, outlet_data_dict=outlet_data_dict)


@bp.route('/admin/delete-outlet/<outlet_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def delete_existing_outlet(outlet_id):
    company_id=current_user.company_id
    outlet_obj = Outlet.query.filter_by(company_id=current_user.company_id).filter_by(id=outlet_id).first()
    admins_obj = Admin.query.filter_by(company_id=company_id).filter_by(outlet_name=outlet_obj.outlet_name).all() # Query Admins who were last used that outlet
    for admin in admins_obj: # Update all Admins outlet, if the outlet they currently are on is deleted
        admin.outlet_name=None    
    db.session.delete(outlet_obj)
    db.session.commit()
    flash(('Successfully deleted outlet'), 'success')
    return redirect(url_for('main.add_new_outlet'))


@bp.route('/admin/change-outlet', methods=['GET', 'POST'])
@login_required(role='admin')
def change_admin_outlet():
    form = UpdateAdminOutletForm()
    company_id = current_user.company_id
    outlets_obj = Outlet.query.filter_by(company_id=company_id).all()
    form.outlet_chosen.choices = [(outlet.outlet_name) for outlet in outlets_obj]
    if form.validate_on_submit():
        outlet_name = form.outlet_chosen.data
        outlet_id = Outlet.query.filter_by(company_id=company_id).filter_by(outlet_name=outlet_name).first().id
        current_user.outlet_id = outlet_id
        current_user.outlet_name = outlet_name
        db.session.commit()
        flash('{} is now your default outlet'.format(outlet_name), 'success')
        return redirect(request.referrer)
    return render_template('main/change_admin_outlet.html', title='test', form=form)



@bp.route('/customer-account-settings', methods=['GET', 'POST'])
@login_required(role='customer')
def customer_settings():
    customer_data = Customer.query.filter_by(id=current_user.id).first().list_customer_data()
    form_update_settings = UpdateCustomerSettingsForm()
    form_password = ResetPasswordForm()
    if request.method == 'GET':
        form_update_settings.name.data = customer_data['name']
        form_update_settings.email.data = customer_data['email']
        form_update_settings.phone.data = customer_data['phone']
    return render_template('customer_settings.html', title='Customer Settings', form_update_settings=form_update_settings, form_password=form_password)


@bp.route('/update-customer-account-settings', methods=['GET', 'POST'])
@login_required(role='customer')
def update_customer_settings():
    form_update_settings = UpdateCustomerSettingsForm()
    form_password = ResetPasswordForm()
    if form_update_settings.validate_on_submit(): # change personal details form
        try:
            phone_number = check_and_clean_phone_number(form_update_settings.phone.data)
        except:
            flash(invalid_phone_number_message(), 'danger')
            return redirect(url_for('main.customer_settings'))
        try:
            current_user.name = form_update_settings.name.data
            current_user.email = form_update_settings.email.data
            current_user.phone = phone_number
            db.session.commit()
            flash('Information successfully updated.', 'success')
            return redirect(url_for('main.customer_settings'))        
        except:
            flash('The email or phone number you keyed in is already taken. Please use something else.', 'danger')
            return redirect(url_for('main.customer_settings'))
    return render_template('customer_settings.html', title='Customer Settings', form_update_settings=form_update_settings, form_password=form_password)


@bp.route('/update-customer-password', methods=['GET', 'POST'])
@login_required(role='customer')
def update_customer_password():
    form_update_settings = UpdateCustomerSettingsForm()
    form_password = ResetPasswordForm()
    if form_password.validate_on_submit(): # reset password form
        try:
            current_user.set_password(form_password.password.data)
        except:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('main.customer_settings'))
        db.session.commit()
        flash('Your password has been changed.', 'success')
        return redirect(url_for('main.customer_settings'))
    return render_template('customer_settings.html', title='Customer Settings', form_update_settings=form_update_settings, form_password=form_password)


@bp.route('/customer-account-deletion', methods=['GET', 'POST'])
@login_required(role='customer')
def delete_customer_account():
    user_id = current_user.id
    user = User.query.filter_by(id=user_id).first()
    customer = Customer.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.delete(customer)
    db.session.commit()
    flash(('Your account has been deleted. All your information has been wiped from our database.', 'danger'))
    return redirect(url_for('main.admin_home'))


@bp.route('/admin-account-settings', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_settings():
    admin_data = Admin.query.filter_by(id=current_user.id).first().list_admin_data()
    form_update_settings = UpdateCustomerSettingsForm()
    form_password = ResetPasswordForm()
    if request.method == 'GET':
        form_update_settings.name.data = admin_data['name']
        form_update_settings.email.data = admin_data['email']
    return render_template('admin_settings.html', title='Admin Settings', form_update_settings=form_update_settings, form_password=form_password)


@bp.route('/update-admin-account-settings', methods=['GET', 'POST'])
@login_required(role='admin')
def update_admin_settings():
    form_update_settings = UpdateAdminSettingsForm()
    form_password = ResetPasswordForm()
    if form_update_settings.validate_on_submit(): # change personal details form
        try:
            current_user.name = form_update_settings.name.data
            current_user.email = form_update_settings.email.data
            db.session.commit()
            flash('Information successfully updated.', 'success')
            return redirect(url_for('main.admin_settings'))        
        except:
            flash('The email you keyed in is already taken. Please use something else.', 'danger')
            return redirect(url_for('main.admin_settings'))
    return render_template('admin_settings.html', title='Admin Settings', form_update_settings=form_update_settings, form_password=form_password)


@bp.route('/update-admin-password', methods=['GET', 'POST'])
@login_required(role='admin')
def update_admin_password():
    form_update_settings = UpdateAdminSettingsForm()
    form_password = ResetPasswordForm()
    if form_password.validate_on_submit(): # reset password form
        try:
            current_user.set_password(form_password.password.data)
        except:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('main.admin_settings'))
        db.session.commit()
        flash('Your password has been changed.', 'success')
        return redirect(url_for('main.admin_settings'))
    return render_template('admin_settings.html', title='Admin Settings', form_update_settings=form_update_settings, form_password=form_password)






# @bp.route('/admin/add-package-company-list', methods=['GET', 'POST'])
# @login_required(role='admin')
# def add_package_to_company_package_list():
#     form = AddCompanyPackageForm()
#     company_id = current_user.company_id
#     if form.validate_on_submit():
#         new_package = CompanyPackages(
#             company_id=company_id, 
#             package_name=form.package_name.data,
#             package_price_in_cents=form.package_price.data * 100,
#             )
#         db.session.add(new_package)
#         db.session.commit()
#         flash(('New package "{}" added to company!'.format(form.package_name.data)))
#         # send_package_invoice_email(current_user)
#         return redirect(url_for('main.display_items'))
#     return render_template('main/register_new_package.html', title='Key in package details', form=form)




