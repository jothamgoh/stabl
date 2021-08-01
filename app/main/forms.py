from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, DecimalField
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, DataRequired, InputRequired
from app.helperfunc import check_and_clean_phone_number
from flask_login import current_user
from app.models import Company


def get_company_packages():
    company_id = current_user.company_id
    package_choices = []
    company_packages_obj = Company.query.filter_by(id=company_id).first().company_packages.all()
    [package_choices.append(p.package_name) for p in company_packages_obj]
    return package_choices

# package_choices = ['Haircut men', 'Haircut women']

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


class AddCompanyPackageForm(FlaskForm): # packages and services are the same thing
    package_name = StringField(('Service Name'), validators=[DataRequired()])
    package_price = DecimalField(('Service Price (SGD)'), validators=[InputRequired()], places=2) 
    submit = SubmitField(('Register new service'))


class AddCompanyProductForm(FlaskForm):
    product_name = StringField(('Item Name'), validators=[DataRequired()])
    product_price = DecimalField(('Item Price (SGD)'), validators=[InputRequired()], places=2) 
    submit = SubmitField(('Register new item'))


# class SearchCustomerForm(FlaskForm):
#     phone_or_email = StringField(('Phone Number or Email'), validators=[DataRequired()])
#     submit = SubmitField(('Search for Customer'))