import phonenumbers


def check_and_clean_phone_number(number):
    number = phonenumbers.parse(number, 'SG')
    if phonenumbers.is_valid_number(number):
            return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
