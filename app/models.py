from sqlalchemy.orm import backref
from app import db, login
from datetime import datetime
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import phonenumbers
from flask import jsonify

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(15))

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

    def check_phone(self, phone):
        number = phonenumbers.parse(phone, 'SG')
        return phonenumbers.is_valid_number(number)


    __mapper_args__ = {
        'polymorphic_identity':'customer',
    }


class Admin(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)    
    password_hash = db.Column(db.String(128))
    package_sold = db.relationship('Package', backref='admin', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    __mapper_args__ = {
        'polymorphic_identity':'admin',
    }


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id')) # which admin created the package
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id')) # which customer used the package
    package_name = db.Column(db.String(128))
    package_total_uses_at_start = db.Column(db.Integer) # number of total uses of package at the start
    package_uses_left_when_keyed = db.Column(db.Integer) # number of uses when package keyed in - for migration into stabl
    package_num_times_used_after_keyed = db.Column(db.Integer, default=0) # number of times customer used package after migration into stabl
    package_price_paid_in_cents = db.Column(db.Integer) # price customer paid
    currency = db.Column(db.String(16), default='SGD')
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=1)
    package_usage = db.relationship('PackageUse', backref='package', lazy='dynamic')

    def __repr__(self):
        return '<Package {}>'.format(self.id)

    def list_customer_package_data(self):
        return {
            'package_id': self.id,
            'package_total_uses_at_start': self.package_total_uses_at_start,
            'package_name': self.package_name,
            'num_uses_left': (self.package_uses_left_when_keyed - self.package_num_times_used_after_keyed),
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