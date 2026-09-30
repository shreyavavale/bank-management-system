from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import BankAccount, Customer, Transaction


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "customer_id", "full_name", "date_of_birth", "gender",
            "phone", "email", "address", "created_at",
        ]
        read_only_fields = ["customer_id", "created_at"]


class BankAccountSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "account_number", "customer", "customer_name", "account_type",
            "opening_balance", "current_balance", "status", "created_at",
        ]
        read_only_fields = ["account_number", "current_balance", "created_at"]

    def validate(self, attrs):
        # Balances must not be changed after the account is created
        if self.instance and "opening_balance" in attrs:
            if attrs["opening_balance"] != self.instance.opening_balance:
                raise serializers.ValidationError(
                    {"opening_balance": "Opening balance cannot be changed."}
                )
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source="account.account_number", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "transaction_id", "account_number", "transaction_type", "amount",
            "balance_after_transaction", "transaction_date", "remarks",
        ]
        read_only_fields = fields


class MoneyTransferSerializer(serializers.Serializer):
    """Input for POST /api/deposits/ and POST /api/withdrawals/."""

    account = serializers.PrimaryKeyRelatedField(queryset=BankAccount.objects.all())
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    txn_type = None  # set by subclasses

    def create(self, validated_data):
        account = validated_data["account"]
        try:
            if self.txn_type == "DEPOSIT":
                return account.deposit(validated_data["amount"])
            return account.withdraw(validated_data["amount"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": exc.messages})

    def to_representation(self, instance):
        return TransactionSerializer(instance).data


class DepositSerializer(MoneyTransferSerializer):
    txn_type = "DEPOSIT"


class WithdrawalSerializer(MoneyTransferSerializer):
    txn_type = "WITHDRAWAL"
