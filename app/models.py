from sqlalchemy.orm import backref
from app import db, login
from flask import current_app
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from time import time


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    outlet = db.relationship('Outlet', backref='company', lazy='dynamic')
    admin = db.relationship('Admin', backref='company', lazy='dynamic')
    package = db.relationship('Package', backref='company', lazy='dynamic')
    company_packages_and_products = db.relationship('CompanyPackagesAndProducts', backref='company', lazy='dynamic')
    customer_orders = db.relationship('CustomerOrders', backref='company', lazy='dynamic') # all services and items bought excluding those which are part of a package

    def __repr__(self):
        return '{}'.format(self.name)


class Outlet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id')) # which company does this Shop belong to
    admin = db.relationship('Admin', backref='outlet', lazy='dynamic')
    customer_orders = db.relationship('CustomerOrders', backref='outlet', lazy='dynamic') # all services and items bought excluding those which are part of a package
    package = db.relationship('Package', backref='outlet', lazy='dynamic') # which outlet was the package created at
    outlet_country = db.Column(db.String(16), default='SG')
    outlet_name = db.Column(db.String(64))
    postal = db.Column(db.String(64))
    unit_number = db.Column(db.String(64), nullable=True)
    address = db.Column(db.String(64))
    phone = db.Column(db.String(64))
    email = db.Column(db.String(120))    

    def list_outlet_attributes(self):
        return {
            "outlet_id": self.id,
            "outlet_country": self.outlet_country,
            "outlet_name": self.outlet_name,
            "postal": self.postal,
            "unit_number": self.unit_number,
            "address": self.address,
            "phone": self.phone,
            "email": self.email
        }


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_use = db.relationship('PackageUse', backref='user', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(15))

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }

class Customer(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    package_bought = db.relationship('Package', backref='customer', lazy='dynamic') # all package orders only
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)    
    phone = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def list_customer_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email
        }

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Customer.query.get(id)

    __mapper_args__ = {
        'polymorphic_identity':'customer',
    }


class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id')) # which company does this admin belong to
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=True) # which outlet does this admin belong to. "Last used" outlet the Admin was tagged to
    outlet_name = db.Column(db.String(64), nullable=True) # outlet name which is tagged to outlet_id
    package_sold = db.relationship('Package', backref='admin', lazy='dynamic')
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)    
    password_hash = db.Column(db.String(128))
    cust_orders = db.relationship('CustomerOrders', backref='admin', lazy='dynamic') # all services and items bought excluding those which are part of a package
    is_superadmin = db.Column(db.Boolean, default=0)
    is_active = db.Column(db.Boolean, default=1)


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def list_admin_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_superadmin': self.is_superadmin,
            'is_active': self.is_active
        }

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Admin.query.get(id)

    __mapper_args__ = {
        'polymorphic_identity':'admin',
    }


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id')) # which company does this admin belong to
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=True) # which company does this admin belong to
    outlet_name = db.Column(db.String(64)) # outlet name which is tagged to outlet_id
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True) # which admin created the package
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id')) # which customer used the package
    package_usage = db.relationship('PackageUse', backref='package', lazy='dynamic')
    package_name = db.Column(db.String(128))
    package_num_total_uses_at_start = db.Column(db.Integer) # number of total uses of package at the start
    package_num_used_when_keyed = db.Column(db.Integer, default=0) # number of uses when package keyed in
    package_num_times_used_after_keyed = db.Column(db.Integer, default=0) # number of times customer used package after migration into stabl
    package_num_times_transferred = db.Column(db.Integer, default=0) # number of times customer had transferred the package to their friend
    package_price_paid_in_cents = db.Column(db.Integer, nullable=True) # price customer paid
    currency = db.Column(db.String(16), default='SGD')
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=1)
    is_ported_over = db.Column(db.Boolean, default=0) # package was ported over by an admin
    is_transferred = db.Column(db.Boolean, default=0) # package was transferred from another customer
    transferred_from_package_id = db.Column(db.Integer, nullable=True) # phone number of the customer who transferred package

    def __repr__(self):
        return '<Package {}>'.format(self.id)

    def num_uses_left(self):
        return (self.package_num_total_uses_at_start - self.package_num_used_when_keyed - self.package_num_times_used_after_keyed - self.package_num_times_transferred)

    def list_customer_package_data(self):
        return {
            'package_id': self.id,
            'company': self.company,
            'outlet_id': self.outlet_id,
            'outlet_name': self.outlet_name,
            'package_name': self.package_name,
            'package_num_total_uses_at_start': self.package_num_total_uses_at_start,
            'package_num_used_when_keyed': self.package_num_used_when_keyed,
            'package_num_times_used_after_keyed': self.package_num_times_used_after_keyed,
            'package_num_times_transferred': self.package_num_times_transferred,
            'num_uses_left': (self.num_uses_left()),
            'created_at': self.created_at,
            'currency': self.currency,
            'package_price_paid_in_cents': self.package_price_paid_in_cents,
            'is_active': self.is_active
        }


class PackageUse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    who_used_package = db.Column(db.Integer, db.ForeignKey('user.id')) # if is_package_transfer = 0, 'user_id' is the person who clicked "use package". if is_package_transfer=1, then 'user_id' is the person you transfer to package to, or package is trasferred from
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    num_uses = db.Column(db.Integer) # number of uses for the package. A normal use is 1, a transfer can be 1 or more. If num_uses is negative, package transferred from someone else, in which case 'who_used_package' is the transferee
    is_package_transfer = db.Column(db.Boolean, default=0) # package was transferred from another customer, or transferred back to the original owner

    def __repr__(self):
        return '<Package usage {}>'.format(self.id)

    def list_package_use_data(self):
        return {
            'who_used_package': self.who_used_package,
            'package_id': self.package_id,
            'created_at': self.created_at,
            'num_uses': self.num_uses,
            'is_package_transfer': self.is_package_transfer
        }


class CompanyPackagesAndProducts(db.Model): # Get company packages list for form input
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id')) # which company does this Package belong to
    customer_orders = db.relationship('CustomerOrders', backref='customerorders', lazy='dynamic') # all services and items bought excluding those which are part of a package
    item_name = db.Column(db.String(128), nullable=False)
    item_price_in_cents = db.Column(db.Integer, nullable=True) # default price of package
    item_type = db.Column(db.String(128), nullable=False) # either "service" or "product"

    def list_item_attributes(self):
        return {
            "item_id": self.id,
            "item_name": self.item_name,
            "item_price_in_cents": self.item_price_in_cents,
            "item_type": self.item_type
        }


class CustomerOrders(db.Model): # table to conslidate all cust orders
    id = db.Column(db.Integer, primary_key=True) # order id
    order_number = db.Column(db.Integer) # order number for the company
    company_id = db.Column(db.Integer, db.ForeignKey('company.id')) # which company does this Package belong to
    outlet_id = db.Column(db.Integer, db.ForeignKey('outlet.id'), nullable=True) # which outlet was the package created at
    outlet_name = db.Column(db.String(64)) # outlet name which is tagged to outlet_id
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id')) # which admin created the package
    package_or_product_id = db.Column(db.Integer, db.ForeignKey('company_packages_and_products.id')) # this uses snake case by default!!!
    item_name = db.Column(db.String(128))
    price_per_item_in_cents = db.Column(db.Integer, nullable=True) # price customer paid for package
    discount_per_item_in_cents = db.Column(db.Integer, nullable=True) # discount for each item
    quantity = db.Column(db.Integer, nullable=False, default=1) # price customer paid for package
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(64), nullable=False) # either 'completed', 'cancelled', or 'refunded'


@login.user_loader
def load_user(id):
    return User.query.get(int(id))