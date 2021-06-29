from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import Admin, Customer
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


class AdminLoginForm(FlaskForm):
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[DataRequired()])
    remember_me = BooleanField(('Remember Me'))
    submit = SubmitField(('Sign In'))


class AdminRegistrationForm(FlaskForm):
    name = StringField(('Name'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        ('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(('Register'))

    def validate_email(self, email):
        user = Admin.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(('Email address is already registered.'))


class AdminResetPasswordRequestForm(FlaskForm):
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(('Request Password Reset'))


class AdminResetPasswordForm(FlaskForm):
    password = PasswordField(('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        ('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(('Request Password Reset'))


class CustomerLoginForm(FlaskForm):
    phone = StringField(('Phone Number'), validators=[DataRequired()])
    remember_me = BooleanField(('Remember Me'))
    submit = SubmitField(('Get OTP'))

class CustomerOTPForm(FlaskForm):
    otp = StringField(('OTP'), validators=[DataRequired()])
    submit = SubmitField(('Submit OTP'))


class CustomerRegistrationForm(FlaskForm):
    name = StringField(('Name'), validators=[DataRequired()])
    phone = StringField(('Phone Number'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired()])
    password = PasswordField(('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        ('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(('Register'))

    def validate_email(self, email):
        user = Customer.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(('Email address is already registered.'))

    def validate_phone(self, phone):
        user = Customer.query.filter_by(phone=phone.data).first()
        if user is not None:
            raise ValidationError(('Phone number is already registered.'))
