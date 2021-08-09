from app.main import bp
from app import db
from flask import render_template, flash, session, redirect, url_for
from app.decorators import login_required
from app.models import Company, Customer, Package, PackageUse, User, Admin, CompanyPackagesAndProducts, CustomerOrders
from app.main.forms import CreateProductOrderForm, RegisterPackageForm, PortCustomerAndPackageForm, TransferPackageForm, AddCompanyPackageForm, AddCompanyProductForm, CreateProductOrderForm
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
    return render_template('admin_home.html', title='Home')


@bp.route('/home', methods=['GET', 'POST'])
@login_required(role='customer')
def customer_home():
    # list package data
    packages = Package.query.filter_by(cust_id=current_user.id).all()
    package_data = [package.list_customer_package_data() for package in packages]
    return render_template('customer_home.html', title='Home', package_data=package_data)
    

@bp.route('/admin/new-package', methods=['GET', 'POST'])
@login_required(role='admin')
def register_new_package():
    form = RegisterPackageForm()
    company_id = current_user.company_id
    # populate package_choices
    company_packages_obj = Company.query.filter_by(id=company_id).first().company_packages_and_products.all()
    form.package_name.choices = [(p.item_name) for p in company_packages_obj if (p.item_type=='package')]
    if form.validate_on_submit():
        phone_number = check_and_clean_phone_number(form.phone.data)
        cust_id = check_if_cust_exists_else_create_return_custid(phone=phone_number)
        package_num_total_uses_at_start = form.package_num_total_uses_at_start.data
        package_num_used_when_keyed = form.package_num_used_when_keyed.data
        package_price_paid_in_cents = int((form.package_price_paid.data) * 100)
        company_id = company_id

        if package_num_total_uses_at_start <= package_num_used_when_keyed or package_price_paid_in_cents < 0:
            flash(('The data you entered does not make sense. Please check and try again.'))
            return redirect(url_for('main.register_new_package'))
        new_package = Package(
            admin_id=current_user.get_id(), 
            cust_id=cust_id,
            company_id=company_id,
            package_name=form.package_name.data,
            package_num_total_uses_at_start=package_num_total_uses_at_start,
            package_num_used_when_keyed=package_num_used_when_keyed,
            package_price_paid_in_cents=package_price_paid_in_cents
            )
        db.session.add(new_package)
        db.session.commit()
        flash(('You have created a package for customer with phone number: {}'.format(phone_number)))
        # send_package_invoice_email(current_user)
        return redirect(url_for('main.admin_home'))
    return render_template('main/register_new_package.html', title='Key in package details', form=form)


@bp.route('/package/use-package/<package_id>', methods=['GET', 'POST'])
@login_required(role='customer')
def use_package(package_id):
    package_user_id = current_user.id
    package_user_role = User.query.filter_by(id=package_user_id).first().role

    p = Package.query.filter_by(id=package_id).first_or_404()

    num_uses_left = p.num_uses_left()
    if num_uses_left <= 0:
        p.is_active = 0
        db.session.commit()
        flash('You have finished using this package.')
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
        flash('Congrats! You have used this package')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    return render_template('customer_home.html', title='Home')


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
            flash('You cannot transfer a package to your own phone number.')
            return redirect(url_for('main.transfer_package', package_id=package_id))
        num_uses_to_transfer = form.num_uses_to_transfer.data
        if num_uses_left < num_uses_to_transfer: # not possible, redirect to same page
            flash('You cannot transfer more uses than what you have. Please try again')
            return redirect(url_for('main.transfer_package', package_id=package_id))
        else: 
            if num_uses_left==num_uses_to_transfer:
                p.is_active = 0
            p.package_num_times_transferred += num_uses_to_transfer
            new_cust_id = check_if_cust_exists_else_create_return_custid(phone=phone_number)
            new_package_for_transferee = Package(
                admin_id=None,
                cust_id=new_cust_id,
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

            flash('You have transferred {} package/s to phone number: {}'.format(num_uses_to_transfer, phone_number))
            return redirect(url_for('main.customer_home'))
    return render_template('main/transfer_package.html', title='Transfer package to a friend', form=form, package_data=package_data) 


@bp.route('/package/package-summary/<package_id>', methods=['GET', 'POST'])
@login_required()
def display_package_summary(package_id):
    package = Package.query.filter_by(id=package_id).first_or_404()
    package_data = package.list_customer_package_data()
    
    package_use_list = package.package_usage.order_by(PackageUse.created_at.desc()).all()
    package_use_data = [package_use.list_package_use_data() for package_use in package_use_list]

    return render_template('main/package_summary.html', title='Package Summary', package_data=package_data, package_use_data=package_use_data)


@bp.route('/admin/port-package', methods=['GET', 'POST'])
@login_required(role='admin')
def port_customer_and_package():
    form = PortCustomerAndPackageForm()
    # populate package_choices
    company_id = current_user.company_id
    company_packages_obj = CompanyPackagesAndProducts.query.filter_by(company_id=company_id).filter_by(item_type='package').all()
    form.package_name.choices = [(p.item_name) for p in company_packages_obj]
    if form.validate_on_submit():
        phone_number = check_and_clean_phone_number(form.phone.data)
        cust_id = check_if_cust_exists_else_create_return_custid(phone=phone_number, name=form.name.data)
        new_package  = Package(
            admin_id=current_user.get_id(),
            cust_id=cust_id,
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
        flash('Package successfully ported over. Please confirm details are correct.')
        return redirect(url_for('main.display_package_summary', package_id=package_id))
    return render_template('main/port_customer_and_package.html', title='Port package', form=form)


@bp.route('/package-invoice/<package_id>', methods=['GET'])
@login_required(role='customer')
def display_package_invoice(package_id):
    p = Package.query.filter_by(cust_id=current_user.id).filter_by(id=package_id).first_or_404()
    package_data = p.list_customer_package_data()
    return render_template('main/package_invoice.html', title='Invoice', package_data=package_data)



@bp.route('/admin/display_available_packages', methods=['GET', 'POST'])
@login_required(role='admin')
def display_available_packages():
    # data to render page
    company_id = current_user.company_id
    company_packages = CompanyPackagesAndProducts.query.filter_by(company_id=company_id).filter_by(item_type='package').all()
    company_packages_data = [package.list_item_attributes() for package in company_packages]

    # form data for register package modal
    form = AddCompanyPackageForm()
    if form.validate_on_submit():
        package_price_in_cents = int((form.package_price.data) * 100)
        new_package = CompanyPackagesAndProducts(
            company_id=company_id, 
            item_name=form.package_name.data,
            item_price_in_cents=package_price_in_cents,
            item_type = 'package'
            )
        db.session.add(new_package)
        db.session.commit()
        flash(('New package "{}" added and can now be used.'.format(form.package_name.data)))
        return redirect(url_for('main.display_available_packages'))
    return render_template('main/display_company_packages.html', title='Display Packages', company_packages_data=company_packages_data, form=form)


@bp.route('/admin/display_available_products', methods=['GET', 'POST'])
@login_required(role='admin')
def display_available_products():
    # data to render page
    company_id = current_user.company_id
    company_products = CompanyPackagesAndProducts.query.filter_by(company_id=company_id).filter_by(item_type='product').all()
    company_products_data = [product.list_item_attributes() for product in company_products]

    # form data for register package modal
    form = AddCompanyProductForm()
    if form.validate_on_submit():
        product_price_in_cents = int((form.product_price.data) * 100)
        new_product = CompanyPackagesAndProducts(
            company_id=company_id, 
            item_name=form.product_name.data,
            item_price_in_cents=product_price_in_cents,
            item_type = 'product'
            )
        db.session.add(new_product)
        db.session.commit()
        flash(('New product "{}" added and can now be used.'.format(form.product_name.data)))
        return redirect(url_for('main.display_available_products'))
    return render_template('main/display_company_products.html', title='Display Products', company_products_data=company_products_data, form=form)



@bp.route('/admin/create-new-item', methods=['GET', 'POST'])
@login_required(role='admin')
def add_item():
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
    return redirect(url_for('main.add_item'))



@bp.route('/admin/checkout', methods=['GET', 'POST'])
@login_required(role='admin')
def checkout():
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
            admin_id=d['admin_id'],
            package_or_product_id=d['package_or_product_id'],
            price_per_item_in_cents=d['price_per_item_in_cents'],
            discount_per_item_in_cents=d['discount_per_item_in_cents'],
            quantity=d['quantity'],
            status='completed'
            )
        db.session.add(new_item)
    db.session.commit()
    del session['checkout']
    flash(('Order successful! Please make sure you have collected payment.'))
    return render_template('main/checkout_summary.html', title="Checkout Summary", checkout_data=checkout_data)
    



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
#         return redirect(url_for('main.display_available_packages'))
#     return render_template('main/register_new_package.html', title='Key in package details', form=form)



# @bp.route('/admin/search-customer', methods=['GET', 'POST'])
# @login_required(role='admin')
# def search_for_customer(): # this does not filter customer by company. This filters every customer in the database with Stabl
#     form = SearchCustomerForm()
#     if form.validate_on_submit():
#         # try to find customer using phone or email
#         try: # case when customer keys in phone number
#             phone_number = check_and_clean_phone_number(form.phone_or_email.data) # if email, exception is raised. if phone number is invalid 'None' returned
#             customer = Customer.query.filter_by(phone=phone_number).first()
#             session['phone_or_email'] = phone_number
#         except: # case when customer keys in email or if phone number is invalid
#             customer = Customer.query.filter_by(email=form.phone_or_email.data).first()
#             session['phone_or_email'] = form.phone_or_email.data
#         if customer is None:
#             flash(('Customer email or phone not found. Please try again'))
#             del session['phone_or_email']
#             return redirect(url_for('main.search_for_customer'))
#         session['cust_id'] = customer.id 
#         return redirect(url_for('main.register_new_package'))
#     return render_template('main/search_for_customer.html', title='Find customer', form=form)
