from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import Admin, Customer
from app.helperfunc import check_and_clean_phone_number

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


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        ('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(('Request Password Reset'))


class CustomerLoginForm(FlaskForm):
    phone_or_email = StringField(('Phone Number or Email'), validators=[DataRequired()])
    password = PasswordField(('Password'), validators=[DataRequired()])
    remember_me = BooleanField(('Remember Me'))
    submit = SubmitField(('Sign In'))


class CustomerLoginOTPForm(FlaskForm):
    phone = StringField(('Phone'), validators=[DataRequired()])
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
        try:
            phone_number = check_and_clean_phone_number(phone.data)
        except:
            raise ValidationError(('Phone number is not valid'))
        user = Customer.query.filter_by(phone=phone_number).first()
        if user is not None:
            raise ValidationError(('Phone number is already registered.'))


class InputEmailAndPasswordForm(FlaskForm):
    name = StringField(('Name'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        ('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(('Confirm information'))

    def validate_email(self, email):
        user = Customer.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(('Email address is already registered.'))
