from django.template.defaulttags import NowNode
from rest_framework import serializers

from .models import UserWallet, AccountNumber, WalletTransaction, TransferPin, Transfer
from ..users.serializers import UserSerializer
from .services.payment.utils import generate_payment_reference
from .services.wallet_service import WalletService, verify_user_account_number, verify_user_transfer_pin, verify_amount
from .services.payment.payment import PaymentService
from .services.utils import get_calculated_amount


class AccountNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountNumber
        fields = [
            "account_number", 'number_id',
            'created_at'
        ]

class WalletSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    account_number = AccountNumberSerializer(read_only=True)

    balance_overall = serializers.SerializerMethodField()
    previous_balance = serializers.SerializerMethodField()

    class Meta:
        model = UserWallet
        fields = [
            'wallet_id', "owner",
            'account_number', 'balance_overall', "previous_balance",
            'currency', 'created_at', 'updated_at'
        ]

    def get_balance_overall(self, obj):
        balance = obj.balance
        if balance == 0:
            return 0.00
        return get_calculated_amount(balance)

    def get_previous_balance(self, obj):
        balance = obj.previous_balance
        if balance == 0:
            return 0.00
        return balance / 100

class DepositSerializer(serializers.Serializer):
    amount = serializers.IntegerField(write_only=True, required=True)
    idempotency_key = serializers.CharField(write_only=True, required=True)

    transaction = "deposit"

    def validate_amount(self, value):

        if not isinstance(value, int):
            raise serializers.ValidationError("amount can only be int")
        if value < 100:
            raise serializers.ValidationError("amount can't be less than 100")
        return value

    def validate_idempotency_key(self, value):
        if not isinstance(value, str) or value is None:
            raise serializers.ValidationError("idempotency_key is required for every transaction")
        return value.strip()


    def create(self, validated_data):
        user = self.context['request'].user
        user_wallet = self.context['wallet']

        amount = validated_data['amount'] * 100
        idempotency_key = validated_data['idempotency_key']

        payment_ref = generate_payment_reference()
        transaction_type = None

        if self.transaction == "deposit":
            transaction_type = WalletTransaction.TransactionType.DEPOSIT

        transaction = WalletService().create_transaction(
            user=user, wallet=user_wallet, reference=payment_ref,
            amount=amount, transaction_type=transaction_type,
            idempotency_key=idempotency_key
        )

        if transaction is None:
            raise serializers.ValidationError("no transaction found")

        if transaction and transaction.status != WalletTransaction.TransactionStatus.PROCESSING:
            transaction.status = WalletTransaction.TransactionStatus.PROCESSING
            transaction.save(update_fields=("status",))

        # initialize paystack payment
        payment_service = PaymentService()
        response = payment_service.initialize_payment(
            amount=transaction.amount, reference=transaction.reference,
            meta_data={"user_pk": str(user.pk)}, email=user.email
        )
        return response

class PaymentVerifySerializer(serializers.Serializer):
    payment_reference = serializers.CharField(write_only=True, required=True)

    def validate_payment_reference(self, value):
        if not isinstance(value, str) or value is None:
            raise serializers.ValidationError("payment reference is invalid")
        return value.strip()


    def create(self, validated_data):
        user = self.context['request'].user

        reference = validated_data['payment_reference']
        paystack_service = PaymentService().verify_payment(reference=reference)

        transaction_verification = WalletService().verify_transaction(
            reference=reference, paystack_data=paystack_service)

        if not transaction_verification['status']:
            raise serializers.ValidationError(transaction_verification['message'])

        update_wallet = WalletService().increment_user_wallet(user, paystack_service['data']['amount'])

        return transaction_verification['transaction']

class TransactionSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    class Meta:
        model = WalletTransaction
        fields = [
            "transaction_id", 'wallet',
            "owner", "idempotency_key",
            "reference", "amount", "description",
            'metadata', 'transaction_type', 'status',
            'created_at', 'updated_at'
        ]
    def get_amount(self, obj):
        amount = obj.amount
        if amount == 0:
            return 0
        return  get_calculated_amount(amount)

class TransactionPinSerializer(serializers.ModelSerializer):
    confirm_pin = serializers.CharField(
        write_only=True,
        required=True,
        help_text="pin confirmation",
    )

    class Meta:
        model = TransferPin
        fields = ['pin', 'confirm_pin']

    @staticmethod
    def is_digits_validator(pin):
        if not isinstance(pin, str) or not pin.isdigit():
            raise serializers.ValidationError("transfer pin can only be digits string")

    @staticmethod
    def length_validator(pin: str):
        if len(pin) > 4 or len(pin) < 4:
            raise serializers.ValidationError("transfer pin cannot be less/greater than 4 characters")

    @staticmethod
    def match(pin, confirm_pin):
        if pin != confirm_pin:
            return False
        return True

    def validate_pin(self, value):
        TransactionPinSerializer().is_digits_validator(value)
        TransactionPinSerializer().length_validator(value)
        return value

    def validate_confirm_pin(self, value):
        TransactionPinSerializer().is_digits_validator(value)
        TransactionPinSerializer().length_validator(value)
        return value

    def validate(self, data):

        first_pin = data['confirm_pin']
        second_pin = data['pin']
        if not TransactionPinSerializer().match(pin=first_pin, confirm_pin=second_pin):
            raise serializers.ValidationError("Pin mismatch")
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_pin")
        user = self.context['request'].user
        user_pin = WalletService().create_transaction_pin(user, validated_data)
        return validated_data

class TransferSerializer(serializers.ModelSerializer):

    transaction = "transfer"

    account_number = serializers.CharField(
        write_only=True,
        required=True,
        help_text="recipient account number",
    )
    transaction_pin = serializers.CharField(
        write_only=True, required=True,
        help_text="Your transfer pin"
    )
    idempotency_key = serializers.CharField(
        write_only=True, required=True,
        help_text="one time idempotency key"
    )
    amount = serializers.DecimalField(
        max_digits=8, decimal_places=2,
        write_only=True,required=True
    )
    class Meta:
        model = Transfer
        fields = [
            "amount", "account_number",
            "transaction_pin", 'idempotency_key'
        ]

    def validate_idempotency_key(self, value):
        DepositSerializer().validate_idempotency_key(value)
        return value

    def validate_transaction_pin(self, value):
        TransactionPinSerializer().is_digits_validator(value)
        TransactionPinSerializer().length_validator(value)

        user = self.context['request'].user

        validated_user_pin = verify_user_transfer_pin(user, value)
        if not validated_user_pin['status']:
            raise serializers.ValidationError(validated_user_pin['message'])

        return value

    def validate_amount(self, value):
        user = self.context['request'].user
        amount_is_valid = verify_amount(user, value)
        if not amount_is_valid['status']:
            raise serializers.ValidationError(amount_is_valid['message'])
        if value < 100:
            raise serializers.ValidationError("amount can't be less that 100")
        return value

    def validate_account_number(self, value):
        TransactionPinSerializer().is_digits_validator(value)
        if len(value) < 10 or len(value) > 10:
            raise serializers.ValidationError("account number must be equal 10 digits")

        user = self.context['request'].user
        validated_account = verify_user_account_number(value, user)
        if not validated_account['status']:
            raise serializers.ValidationError(validated_account['message'])
        return value

    def create(self, validated_data):
        current_user = self.context['request'].user

        validated_account = verify_user_account_number(validated_data['account_number'], current_user)
        account_owner = validated_account['owner']

        reference = generate_payment_reference()
        idempotency_key = validated_data['idempotency_key']
        amount = validated_data['amount'] * 100

        transfer = WalletService().create_transfer(
            sender_wallet=current_user.wallet,
            receiver_wallet=account_owner.wallet,
            idempotency_key=idempotency_key, amount=amount,
            reference=reference,
        )
        if transfer:
            transfer.status = Transfer.TransferStatus.PROCESSING
            transfer.save(update_fields=['status'])

        # create transaction
        transaction_type = None

        if self.transaction == "transfer":
            transaction_type = WalletTransaction.TransactionType.TRANSFER

        transaction = WalletService().create_transaction(
            user=current_user, wallet=current_user.wallet, reference=reference,
            amount=amount, transaction_type=transaction_type,
            idempotency_key=idempotency_key
        )

        if transaction is None:
            raise serializers.ValidationError("no transaction found")

        if transaction and transaction.status != WalletTransaction.TransactionStatus.PROCESSING:
            transaction.status = WalletTransaction.TransactionStatus.PROCESSING
            transaction.save(update_fields=("status",))

        return validated_data

class TransferVerifySerializer(serializers.ModelSerializer):

    payment_reference = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = Transfer
        fields = ['payment_reference']

    def validate_payment_reference(self, value):
        if not isinstance(value, str) or value is None:
            raise serializers.ValidationError("payment reference is invalid")
        return value.strip()

    def create(self, validated_data):

        reference = validated_data['payment_reference']
        transfer_data = WalletService().fetch_transfer_by_reference(reference=reference)

        transaction_verification = WalletService().verify_transaction(
            reference=reference, paystack_data=transfer_data)

        if not transaction_verification['status']:
            raise serializers.ValidationError(transaction_verification['message'])

        transfer = None
        try:
            transaction = transaction_verification['transaction']
            transfer = Transfer.objects.get(reference=reference)
            transfer.status = transaction.status
        except Exception as exc:
            raise serializers.ValidationError(str(exc))


        if transfer.status == Transfer.TransferStatus.SUCCESS:
            # debit/credit users
            sender = transfer.sender_wallet
            receiver = transfer.receiver_wallet

            sender_wallet = WalletService().decrement_user_wallet(user_wallet=sender, amount=transfer.amount)
            receiver_wallet = WalletService().increment_user_wallet(user_wallet=receiver, amount=transfer.amount)


        return transaction








