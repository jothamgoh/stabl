from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, DecimalField, DateField
from wtforms.validators import ValidationError, DataRequired, InputRequired
from app.models import Admin, Customer, Package, PackageUse


package_choices = ['Haircut men', 'Haircut women']

class SearchCustomerForm(FlaskForm):
    phone_or_email = StringField(('Phone Number or Email'), validators=[DataRequired()])
    submit = SubmitField(('Search for Customer'))


class RegisterPackageForm(FlaskForm):
    package_name = SelectField(('Package Name'), validators=[DataRequired()], choices=package_choices)
    package_num_total_uses_at_start = IntegerField(('No. times package can be used'), validators=[DataRequired()])
    package_num_used_when_keyed = IntegerField(('No. times package has already been used'), validators=[InputRequired()])
    package_price_paid = DecimalField(('Price Paid for Package (SGD)'), validators=[InputRequired()], places=2)
    submit = SubmitField(('Register package for customer'))


class PortCustomerAndPackageForm(FlaskForm):
    phone = StringField(('Customer Phone Number'), validators=[DataRequired()])
    name = StringField(('Customer Name'))
    package_name = SelectField(('Package Name'), validators=[DataRequired()], choices=package_choices)
    package_num_total_uses_at_start = IntegerField(('No. times package can be used'), validators=[DataRequired()])
    package_num_used_when_keyed = IntegerField(('No. times package has already been used'), validators=[InputRequired()])
    package_price_paid = DecimalField(('Price Paid for Package (SGD)'), places=2)
    created_at = DateField('Date Package Created (YYYY-MM-DD e.g. 2021-01-30)', format='%Y-%m-%d')
    submit = SubmitField(('Port new package'))
