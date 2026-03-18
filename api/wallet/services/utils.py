import random
import string
import bcrypt
from rest_framework.exceptions import ValidationError

def generate_account_number():

    digits_to_generate_from = string.digits
    number: tuple = "58", "".join(random.choice(digits_to_generate_from) for _ in range(8))
    valid_account_number = number[0] + number[1]
    if len(valid_account_number) != 10:
        raise ValidationError("Invalid Account Number")

    return valid_account_number.strip()

def hash_account_number(number: str):

    if  not isinstance(number, str) or not number:
        raise ValidationError("account number cannot be a non-empty string")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(number.encode("utf-8"), salt)
    return hashed

def verify_hashed_account(number, hashed_account_number) -> bool:
    if not isinstance(number, str) or not number:
        return False

    if isinstance(hashed_account_number, str):
        return bcrypt.checkpw(number.encode("utf-8"), hashed_account_number.encode("utf-8"))
    return bcrypt.checkpw(number.encode("utf-8"), hashed_account_number)


def get_calculated_amount(amount):
    return amount / 100



