import phonenumbers
from flask import flash, redirect, url_for, render_template

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