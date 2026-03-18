
from django.db import transaction
from django.utils import timezone


from .utils import hash_account_number, verify_hashed_account
from .payment.utils import get_data
from ..models import AccountNumber, UserWallet, WalletTransaction, TransferPin, Transfer

import logging


logger = logging.getLogger(__name__)

def verify_amount(user, amount):
    if user is None:
        raise ValueError("user instance must be present")
    if amount is None:
        raise ValueError("amount must be present")
    wallet = UserWallet.objects.get(owner=user)
    if wallet.balance / 100 < amount:
        return {"status": False, "message": "insufficient funds"}
    return {'status': True, "message": "valid"}

def verify_user_transfer_pin(user, pin):
    if user is None:
        raise ValueError("user instance must be present")
    try:
        transfer_pin = TransferPin.objects.get(owner=user, pin=pin)
    except TransferPin.DoesNotExists:
        return {"status": False, "message": "pin not found, invalid"}
    if not verify_hashed_account(pin, transfer_pin.hashed_pin):
        return {"status": False, "message": "invalid pin"}
    return {"status": True, "message": "valid"}

def verify_user_account_number(account_number, user):
    if not isinstance(account_number, str) or account_number is None:
        raise ValueError("account number must be present")

    try:
        account_number_instance = AccountNumber.objects.get(account_number=account_number)
    except AccountNumber.DoesNotExists:
        return {"status": False, "message": "this account is Invalid"}

    if not verify_hashed_account(account_number, account_number_instance.hashed):
        return {"status": False, "message": "invalid account number"}
    if account_number_instance.wallet.owner == user:
        return {"status": False, 'message': 'you cannot send to your self'}

    return {"status": True, "message": "account_found", "owner": account_number_instance.wallet.owner}


class WalletService:
    def __init__(self):
        pass

    @transaction.atomic
    def create_account_number(self, account_number):
        if not isinstance(account_number, str) or account_number is None:
            raise ValueError("account_number must be a string")

        try:
            hashed_account_number = hash_account_number(account_number)

            new_account_instance = AccountNumber.objects.create(
                account_number=account_number,
                hashed=hashed_account_number
            )
            logger.info("account number created and saved {}".format(new_account_instance.pk))
        except Exception as  e:
            logger.exception(e)
            raise Exception(e)

        return new_account_instance

    @transaction.atomic
    def create_user_wallet(self, user, account_number):
        if user is None or account_number is None:
            raise ValueError("User and/or Account number must be provided")

        try:
            wallet = UserWallet.objects.create(
                owner=user, account_number=account_number
            )
            if not  wallet.balance == 0:
                raise ValueError("Balance must be zero on wallet creation")
            logger.info(f'User wallet created for user: {user.username}')
        except Exception as e:
            logger.exception(f"exception on wallet creation: {e}")
            raise Exception(str(e))
        return wallet

    def increment_user_wallet(self, user = None, user_wallet = None, amount = 0):
        if user is None:
            user_wallet = user_wallet
        else:
            user_wallet = user.wallet
        balance = user_wallet.balance

        with transaction.atomic():
            user_wallet.balance += amount
            user_wallet.previous_balance = balance
            user_wallet.updated_at = timezone.now()
            user_wallet.save(update_fields=("balance", "previous_balance", "updated_at"))

        return user_wallet

    def decrement_user_wallet(self, user = None, user_wallet = None, amount = 0):
        if user is None:
            user_wallet = user_wallet
        else:
            user_wallet = user.wallet

        balance = user_wallet.balance

        with transaction.atomic():
            user_wallet.balance -= amount
            user_wallet.previous_balance = balance
            user_wallet.updated_at = timezone.now()
            user_wallet.save(update_fields=("balance", "previous_balance", "updated_at"))

        return user_wallet

    @transaction.atomic
    def create_transfer(self, sender_wallet, receiver_wallet, reference, idempotency_key, amount):
        if sender_wallet is None or receiver_wallet is None:
            raise ValueError("sender/receiver must both be present")
        if reference is None or idempotency_key is None or amount is None:
            raise ValueError("both reference, idempotency key and amount is required")

        try:
            transfer_instance = Transfer.objects.create(
                sender_wallet=sender_wallet, receiver_wallet=receiver_wallet,
                amount=amount, reference=reference
            )
            logger.info("Transfer initiated")
        except Exception as e:
            logger.exception(str(e))
            raise Exception(e)
        return transfer_instance

    @transaction.atomic
    def create_transaction(self, user, wallet, reference, amount, transaction_type, idempotency_key):
        if user is None or wallet is None:
            raise ValueError("User and/or Account number must be provided")
        if amount is None or reference is None:
            raise ValueError("You can't create a transaction without a payment reference")

        transaction = None

        try:
            if WalletTransaction.objects.filter(owner=user, idempotency_key=idempotency_key, status=WalletTransaction.TransactionStatus.PROCESSING).exists():
                transaction = WalletTransaction.objects.get(owner=user, idempotency_key=idempotency_key)
            else:

                transaction = WalletTransaction.objects.create(
                    owner=user, wallet=wallet, idempotency_key=idempotency_key, reference=reference,
                    amount=amount, transaction_type=transaction_type
                )
            logger.info(f"Transaction created for user {user.get_display_name()}")
        except WalletTransaction.DoesNotExist:
            return None
        except Exception as e:
            logger.exception(f"Failed to Execute transaction {e}")
            raise Exception(e)

        return transaction

    def already_failed(self, transaction):
        if transaction.status == WalletTransaction.TransactionStatus.FAILED:
            return True
        return False

    def already_succeeded(self, transaction):
        if transaction.status == WalletTransaction.TransactionStatus.SUCCESS:
            return True
        return False

    @transaction.atomic
    def save_success_transaction(self, wallet_transaction, message, meta_data):
        if not isinstance(wallet_transaction, WalletTransaction):
            raise ValueError("not a valid transaction instance")

        try:
            wallet_transaction.description = message
            wallet_transaction.metadata = meta_data
            wallet_transaction.status = WalletTransaction.TransactionStatus.SUCCESS

        except Exception as e:
            raise   Exception(e)

        wallet_transaction.save(update_fields=['status', 'description', 'metadata'])

    @transaction.atomic()
    def save_failed_transaction(self, wallet_transaction, message, meta_data):
        if not isinstance(wallet_transaction, WalletTransaction):
            raise ValueError("not a valid transaction instance")

        try:
            wallet_transaction.description = message
            wallet_transaction.metadata = meta_data
            wallet_transaction.status = WalletTransaction.TransactionStatus.FAILED

        except Exception as e:
            raise Exception(e)

        wallet_transaction.save(update_fields=['status', 'description', 'metadata'])

    def verify_transaction(self, reference, paystack_data):
        data = paystack_data['data']
        status = paystack_data['status']
        with transaction.atomic():
            wallet_transaction = WalletTransaction.objects.select_for_update().get(reference=reference)
            if self.already_failed(wallet_transaction):
                return {"status": False, "message": "Transaction Already failed"}

            if self.already_succeeded(wallet_transaction):
                return {"status": False, "message": "Transaction already passed"}

            if not status:
                message = paystack_data['message']
                meta = paystack_data['meta']
                self.save_failed_transaction(wallet_transaction, message, meta)

                logger.info(message)
                return {"status": False, "message": message}

            else:
                message = paystack_data['message']
                amount = data['amount']
                if wallet_transaction.amount != amount:
                    return {"status": False, 'message': 'amount does not match'}

                meta_data = data['log']

                self.save_success_transaction(wallet_transaction, message, meta_data)
                logger.info(message)
                return {"status": True, "message": message, "transaction": wallet_transaction}

    @transaction.atomic
    def create_transaction_pin(self, user, validated_data):
        if not user or not "pin" in validated_data:
            raise ValueError("a user instance is required and pin must be present")

        transaction_pin = validated_data['pin']

        try:
            hashed_pin = hash_account_number(transaction_pin)
            user_transaction_pin = TransferPin.objects.create(
                pin=transaction_pin, hashed_pin=hashed_pin, owner=user
            )
        except Exception as e:
            raise Exception(e)
        return user_transaction_pin

    def fetch_transfer_by_reference(self, reference):

        if reference is None:
            raise ValueError("payment reference must be present")

        try:
            transfer = Transfer.objects.get(reference=reference)
        except Transfer.DoesNotExist:
            return get_data(status=False, message="Transfer does not exist", amount=0.00)

        if self.already_failed(transfer):
            return get_data(status=False, message="transfer failed and closed", amount=transfer.amount)

        if self.already_succeeded(transfer):
            return get_data(status=False, message="transfer passed and closed", amount=transfer.amount)
        return  get_data(status=True, message="Transfer verified", amount=transfer.amount)
