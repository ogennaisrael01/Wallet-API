from django.conf import settings

import requests


class PaymentService:
    PAYSTACK_INITIALIZE_URL = settings.PAYSTACK_INITIALIZE_URL
    PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
    PAYSTACK_VERIFY_PAYMENT = settings.PAYSTACK_VERIFY_PAYMENT

    @classmethod
    def verify_keys(cls):
        if not cls.PAYSTACK_SECRET_KEY:
            raise ValueError("PAYSTACK_SECRET_KEY is required")
        return True

    def get_headers(self):
        try:
            PaymentService().verify_keys()
        except ValueError as e:
            return {"error": str(e)}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {PaymentService().PAYSTACK_SECRET_KEY}"
        }

        return headers

    def initialize_payment(self, amount, reference, meta_data, email):
        # amount is already in subunit here
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if reference is None:
            raise ValueError("Reference cannot be null")
        payment_payload = {
            "amount": float(amount), "reference": reference,
            "meta_data": meta_data, "email": email,
            "currency": "NGN", "channels": ["card", "bank", "bank_transfer"]
        }

        url = PaymentService().PAYSTACK_INITIALIZE_URL
        if url is None:
            raise ValueError("cannot initialize payment without a pay url")

        try:
            response = requests.post(url=url, json=payment_payload, headers=self.get_headers())
        except requests.exceptions.RequestException as e:
            raise ValueError("Payment failed due to {}".format(e))
        except Exception as e:
            raise Exception(str(e))

        return response.json()


    def verify_payment(self, reference):
        if not isinstance(reference, str) or reference is None:
            raise ValueError("payment reference is null")

        self.get_headers().pop("Content-Type")
        headers = self.get_headers()
        url = PaymentService().PAYSTACK_VERIFY_PAYMENT + reference
        print(headers)

        try:
            response = requests.get(url, headers=headers)

        except requests.exceptions.RequestException as e:
            raise ValueError("Payment failed due to {}".format(e))
        except Exception as e:
            raise Exception(str(e))

        return response.json()





