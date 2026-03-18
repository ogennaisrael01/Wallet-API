
import string
import random

from django.utils import timezone


def generate_payment_reference():
    string_to_generate_from = string.hexdigits
    reference = "".join(random.sample(string_to_generate_from, 16))
    return reference


def get_data(status, message, amount):
    return {
        "status": status,
        "message": message,
        "meta": "",
        "data": {
            "amount": amount,
            "log": {
                "current_time": str(timezone.now()),
                "status": message
            }
        }
    }