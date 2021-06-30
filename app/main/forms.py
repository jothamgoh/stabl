from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, DecimalField
from wtforms.validators import ValidationError, DataRequired, InputRequired
from app.models import Admin, Customer, Package, PackageUse

class SearchCustomerForm(FlaskForm):
    phone_or_email = StringField(('Phone Number or Email'), validators=[DataRequired()])
    submit = SubmitField(('Search for Customer'))


class RegisterPackageForm(FlaskForm):
    package_name = SelectField(('Package Name'), validators=[DataRequired()], choices=['Haircut men', 'Haircut women'])
    package_total_uses_at_start = IntegerField(('No. times package can be used'), validators=[DataRequired()])
    package_uses_left_when_keyed = IntegerField(('No. times package was used'), validators=[InputRequired()])
    package_price_paid = DecimalField(('Price Paid for Package (SGD)'), validators=[InputRequired()], places=2)
    submit = SubmitField(('Register package for customer'))