import phonenumbers
from flask import flash, redirect, url_for, render_template
from app.models import Customer
from app import db

def check_and_clean_phone_number(number):
    """
    If email entered, exception thrown. if number entered but not valid, None returned
    """
    try:
        number = phonenumbers.parse(number, 'SG')
        if phonenumbers.is_valid_number(number):
            return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
        raise ValueError('Invalid phone number')
    except:
        raise ValueError('Invalid phone number')

def invalid_phone_number_message():
    return str('Phone number is not a valid Singapore number.')

def check_if_cust_exists_else_create_return_custid(phone, name=""):
    """
    Check if customer exisits. 
    If customer exisits, return cust_id
    If customer does not exist, create new customer, add and flush. Return cust_id. Commit to db after using this function
    """
    customer = Customer.query.filter_by(phone=phone).first()
    if customer is None: # customer does not currently exist. Create new customer
        new_customer = Customer(name=name,phone=phone)
        db.session.add(new_customer)
        db.session.commit()
        cust_id = new_customer.id
    else:
        cust_id = customer.id
    return cust_id
