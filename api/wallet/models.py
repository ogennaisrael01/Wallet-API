
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import gettext_lazy as _

import uuid

UserModel = get_user_model()

class AccountNumber(models.Model):

    number_id = models.UUIDField(
        primary_key=True, unique=True,
        db_index=True, default=uuid.uuid4, editable=False
    )
    account_number = models.CharField(max_length=20, unique=True)
    hashed = models.BinaryField(max_length=32, unique=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"account_number( {self.account_number[:5]}..."

    class Meta:
        verbose_name = _("Account Number")
        verbose_name_plural = _("account numbers")

        indexes = [
            models.Index(fields=['account_number'])
        ]

class TransferPin(models.Model):
    pin_id = models.UUIDField(
        primary_key=True, db_index=True, unique=True,
        editable=False, default=uuid.uuid4)

    pin = models.CharField(max_length=10)
    owner = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name='transfer_pin')
    hashed_pin = models.BinaryField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Pin({self.owner.get_display_name()}, {self.hashed_pin[:8]}...."

    class Meta:
        verbose_name = _("Transaction Pin")
        verbose_name_plural = _("Transaction pins")
        indexes = [
            models.Index(fields=('pin',)),
            models.Index(fields=('hashed_pin',))
        ]


class UserWallet(models.Model):
    wallet_id = models.UUIDField(
        primary_key=True, db_index=True,
        default=uuid.uuid4, editable=False, unique=True
    )
    owner = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="wallet")

    account_number = models.OneToOneField(AccountNumber, on_delete=models.SET_NULL, null=True, related_name="wallet")

    balance =  models.DecimalField(decimal_places=2, max_digits=8, default=0)
    previous_balance = models.DecimalField(decimal_places=2, max_digits=8, default=0)

    currency = models.CharField(blank=True, null=True, max_length=20, default="NGN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"user wallet ({self.owner.get_display_name()}, {self.account_number.account_number[:5]}..."


    class Meta:
        verbose_name = _("User Wallet")
        verbose_name_plural = _("User wallets")

        constraints = [
            models.UniqueConstraint(fields=("owner", "account_number"), name='owner_unique')
        ]

        indexes = [
            models.Index(fields=("balance",)),
            models.Index(fields=("currency",)),
            models.Index(fields=("created_at",)),
            models.Index(fields=('previous_balance',))

        ]


class Transfer(models.Model):

    class TransferStatus(models.TextChoices):
        PROCESSING = 'Processing'
        PENDING = 'Pending'
        FAILED = 'Failed'
        SUCCESS = 'Success'

    transfer_id = models.UUIDField(
        primary_key=True, max_length=20,
        unique=True, editable=False,
        default=uuid.uuid4
    )
    sender_wallet = models.ForeignKey(UserWallet, on_delete=models.DO_NOTHING, related_name="sender_wallet")
    receiver_wallet = models.ForeignKey(UserWallet, on_delete=models.DO_NOTHING, related_name="receiver_wallet")

    status = models.CharField(max_length=50, choices=TransferStatus.choices, default=TransferStatus.PENDING)
    amount = models.DecimalField(decimal_places=2, max_digits=8, default=0) #amount in subunit
    reference = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"Transfer({self.sender_wallet.pk} <-> {self.receiver_wallet.pk}"

    class Meta:
        verbose_name = _("Transfer")
        verbose_name_plural = _("Transfers")

        indexes = [
            models.Index(fields=("status",)),
            models.Index(fields=("amount",)),
            models.Index(fields=("reference",)),
            models.Index(fields=("created_at",))
        ]

class Withdraw(models.Model):

    class WithDrawStatus(models.TextChoices):
        PROCESSING = 'Processing'
        PENDING = 'Pending'
        FAILED = 'Failed'
        SUCCESS = 'Success'

    withdraw_id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False, db_index=True)
    amount = models.DecimalField(decimal_places=2, max_digits=8, default=0)

    status = models.CharField(max_length=50, choices=WithDrawStatus.choices, default=WithDrawStatus.PENDING)
    user_wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='withdraws')

    account_name = models.CharField(max_length=255, null=True)
    bank_code = models.CharField(max_length=50)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=255)

    reference = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"withdraw {self.user_wallet.owner.get_display_name()} -> {self.bank_name}"

    class Meta:
        verbose_name = _("Withdraw")
        verbose_name_plural = _("withdrawals")

        indexes = [
            models.Index(fields=("reference",)),
            models.Index(fields=("amount",)),
            models.Index(fields=("status",)),
            models.Index(fields=("created_at",))
        ]


class WalletTransaction(models.Model):
    transaction_id = models.UUIDField(
        primary_key=True, unique=True, editable=False,
        default=uuid.uuid4, db_index=True
    )
    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name="transaction")

    class TransactionType(models.TextChoices):
        DEPOSIT = "Deposit"
        WITHDRAW = "Withdraw"
        TRANSFER = "Transfer"

    class TransactionStatus(models.TextChoices):
        PROCESSING = 'Processing'
        SUCCESS = "Success"
        PENDING = "Pending"
        FAILED = 'Failed'


    owner = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="transactions")

    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)
    reference = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    transaction_type = models.CharField(max_length=255, choices=TransactionType.choices, default=None, null=True)

    status = models.CharField(max_length=255, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return  f"Transaction {self.transaction_id} for {self.owner.get_display_name()}"

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['amount']),
            models.Index(fields=['reference']),
        ]
        constraints = [
            models.UniqueConstraint(fields=("reference", "owner", 'wallet'), name='owner-reference-unique')
        ]

