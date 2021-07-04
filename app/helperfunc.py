import phonenumbers
from flask import flash, redirect, url_for

def check_and_clean_phone_number(number):
    """
    If email entered, exception thrown. if number entered but not valid, None returned
    """
    number = phonenumbers.parse(number, 'SG')
    if phonenumbers.is_valid_number(number):
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)

# def check_and_clean_phone_number(number, invalid_route_redirect):
#     if clean_phone_number(number=number) is None: # number is invalid
#         flash(('Invalid phone number, please try again'))
#         return redirect(url_for(invalid_route_redirect))
