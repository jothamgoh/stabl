from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, DecimalField
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email
from app.helperfunc import check_and_clean_phone_number
from flask_login import current_user
from app.models import Company


class RegisterPackageForm(FlaskForm):
    phone = StringField(('Customer Phone Number'), validators=[DataRequired()])
    package_name = SelectField(('Package Name'), validators=[DataRequired()])
    package_num_total_uses_at_start = IntegerField(('No. times package can be used'), validators=[DataRequired()])
    package_num_used_when_keyed = IntegerField(('No. times package has already been used'), validators=[InputRequired()])
    package_price_paid = DecimalField(('Price Paid for Package (SGD)'), validators=[InputRequired()], places=2)
    submit = SubmitField(('Register package for customer'))

    def validate_phone(self, phone):
        try:
            check_and_clean_phone_number(phone.data)
        except:
            raise ValidationError(('Phone number is not valid'))


class PortCustomerAndPackageForm(FlaskForm):
    phone = StringField(('Customer Phone Number'), validators=[DataRequired()])
    name = StringField(('Customer Name'))
    package_name = SelectField(('Package Name'), validators=[DataRequired()])
    package_num_total_uses_at_start = IntegerField(('No. times package can be used'), validators=[DataRequired()])
    package_num_used_when_keyed = IntegerField(('No. times package has already been used'), validators=[InputRequired()])
    package_price_paid = DecimalField(('Price Paid for Package (SGD)'), places=2)
    created_at = DateField(format='%Y-%m-%d')
    submit = SubmitField(('Port new package'))

    def validate_phone(self, phone):
        try:
            check_and_clean_phone_number(phone.data)
        except:
            raise ValidationError(('Phone number is not valid'))


class TransferPackageForm(FlaskForm):
    phone = StringField(('Phone Number to transfer to'), validators=[DataRequired()])
    num_uses_to_transfer = IntegerField(('No. package uses to transfer'), validators=[DataRequired()])
    submit = SubmitField(('Transfer to friend'))

    def validate_phone(self, phone):
        try:
            check_and_clean_phone_number(phone.data)
        except:
            raise ValidationError(('Phone number is not valid'))


class AddCompanyItemForm(FlaskForm): # packages and services are the same thing
    item_name = StringField(validators=[DataRequired()])
    item_price = DecimalField(validators=[InputRequired()], places=2) 
    submit = SubmitField(('Register new item'))


class CreateProductOrderForm(FlaskForm):
    item_name = SelectField(('Package Name'), validators=[DataRequired()])
    item_price = DecimalField(('Item Price (SGD)'), validators=[InputRequired()], places=2) 
    item_discount = DecimalField(('Item Discount (SGD)'), places=2) 
    item_quantity = IntegerField(('Quantity'), validators=[DataRequired()]) 
    submit = SubmitField(('Add Product'))


class UpdateCustomerSettingsForm(FlaskForm):
    name = StringField(('Name'), validators=[DataRequired()])
    phone = StringField(('Phone Number'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(('Submit'))


class UpdateAdminSettingsForm(FlaskForm):
    name = StringField(('Name'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(('Submit'))


# class SearchCustomerForm(FlaskForm):
#     phone_or_email = StringField(('Phone Number or Email'), validators=[DataRequired()])
#     submit = SubmitField(('Search for Customer'))