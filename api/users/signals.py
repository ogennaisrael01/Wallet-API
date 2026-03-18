from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from ..wallet.services.utils import generate_account_number
from ..wallet.services.wallet_service import WalletService

UserModel = get_user_model()
import logging

logger = logging.getLogger(__name__)

@receiver(signal=post_save, sender=UserModel)
def auto_create_wallet(sender, instance, created, **kwargs):
    if not created:
        return
    if not isinstance(instance, UserModel):
        return

    # auto save wallet with account number
    account_number = generate_account_number()
    logger.info(f"account number for {instance.username}: {account_number}")

    user_account_number_instance = WalletService().create_account_number(account_number)

    #save user wallet
    wallet = WalletService().create_user_wallet(user=instance, account_number=user_account_number_instance)
    logger.info(f"User wallet created for {instance.username}: wallet: {wallet.pk}")