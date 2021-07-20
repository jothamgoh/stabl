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
    admin = db.relationship('Admin', backref='company', lazy='dynamic')
    package = db.relationship('Package', backref='company', lazy='dynamic')

    def __repr__(self):
        return '{}'.format(self.name)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)    
    phone = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    package_bought = db.relationship('Package', backref='customer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)    
    password_hash = db.Column(db.String(128))
    package_sold = db.relationship('Package', backref='admin', lazy='dynamic')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True) # which admin created the package
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id')) # which customer used the package
    company_id = db.Column(db.Integer, db.ForeignKey('company.id')) # which company does this admin belong to
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
    package_usage = db.relationship('PackageUse', backref='package', lazy='dynamic')

    def __repr__(self):
        return '<Package {}>'.format(self.id)

    def num_uses_left(self):
        return (self.package_num_total_uses_at_start - self.package_num_used_when_keyed - self.package_num_times_used_after_keyed - self.package_num_times_transferred)

    def list_customer_package_data(self):
        return {
            'package_id': self.id,
            'company': self.company,
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
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)


    def __repr__(self):
        return '<Package usage {}>'.format(self.id)





@login.user_loader
def load_user(id):
    return User.query.get(int(id))