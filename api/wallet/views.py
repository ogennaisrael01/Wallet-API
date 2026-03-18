from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import UserWallet
from .permissions import IsWalletOwner
from .serializers import WalletSerializer, DepositSerializer, PaymentVerifySerializer, TransactionSerializer, \
    TransactionPinSerializer, TransferSerializer, TransferVerifySerializer


class WalletViewSet(viewsets.GenericViewSet):
    permission_classes = [IsWalletOwner]

    def get_serializer_class(self):
        if self.action == "deposit":
            return DepositSerializer
        elif self.action == "verify_deposit":
            return PaymentVerifySerializer
        elif self.action == 'set_transaction_pin':
            return TransactionPinSerializer
        elif self.action == 'transfer':
            return TransferSerializer
        elif self.action == "verify_transfer":
            return  TransferVerifySerializer
        return None

    @action(methods=['post'], detail=False)
    def verify_transfer(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        output_serializer = serializer.save()
        return Response(TransactionSerializer(output_serializer).data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def transfer(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "transfer initialized"}, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=False)
    def set_transaction_pin(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': "success", 'message': 'Transaction pin set'}, status=status.HTTP_201_CREATED)


    @action(methods=['post'], detail=False)
    def verify_deposit(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        output = serializer.save()
        return Response(TransactionSerializer(output).data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def deposit(self, request, *args, **kwargs):
        user_wallet = request.user.wallet
        serializer = self.get_serializer(data=request.data,
                                        context={"request": request, 'wallet': user_wallet})
        serializer.is_valid(raise_exception=True)
        output = serializer.save()
        if not output['status']:
            return Response(output, status=status.HTTP_400_BAD_REQUEST)

        return Response(output, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user_wallet = UserWallet.objects\
            .select_related("owner", "account_number")\
            .get(owner=self.request.user)

        if user_wallet is None:
            return UserWallet.objects.none()
        return user_wallet

    @action(methods=['get'], detail=False)
    def wallet(self, request, *args, **kwargs):

        wallet = self.get_queryset()
        if wallet.owner != request.user:
            raise PermissionDenied()

        output_serializer = WalletSerializer(wallet)
        return Response(output_serializer.data, status=status.HTTP_200_OK)







