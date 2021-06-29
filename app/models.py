from app import db, login
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import phonenumbers

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    __mapper_args__ = {
        'polymorphic_identity':'admin',
    }


@login.user_loader
def load_user(id):
    return User.query.get(int(id))