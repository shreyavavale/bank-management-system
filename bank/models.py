import random
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models, transaction
from django.utils import timezone

phone_validator = RegexValidator(
    regex=r"^\d{10}$", message="Phone number must contain exactly 10 digits."
)


class Customer(models.Model):
    GENDER_CHOICES = [("M", "Male"), ("F", "Female"), ("O", "Other")]

    customer_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    email = models.EmailField(unique=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.date_of_birth and self.date_of_birth >= timezone.now().date():
            raise ValidationError({"date_of_birth": "Date of birth must be in the past."})

    def __str__(self):
        return f"{self.full_name} (C{self.customer_id:04d})"


def generate_account_number():
    """Return a unique 12-digit account number that starts with '1000'."""
    while True:
        number = "1000" + "".join(str(random.randint(0, 9)) for _ in range(8))
        if not BankAccount.objects.filter(account_number=number).exists():
            return number


class BankAccount(models.Model):
    ACCOUNT_TYPES = [("SAVINGS", "Savings"), ("CURRENT", "Current")]
    STATUS_CHOICES = [("ACTIVE", "Active"), ("INACTIVE", "Inactive")]

    account_number = models.CharField(
        max_length=12, primary_key=True, default=generate_account_number, editable=False
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="accounts"
    )
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    current_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account_number} - {self.customer.full_name}"

    @property
    def is_active(self):
        return self.status == "ACTIVE"

    # ------------------------------------------------------------------
    # Business logic (kept in the model so views and the REST API share it)
    # ------------------------------------------------------------------
    def _apply(self, txn_type, amount):
        amount = Decimal(amount)
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        with transaction.atomic():
            # re-read the row inside the transaction so the balance is fresh
            account = BankAccount.objects.select_for_update().get(pk=self.pk)
            if account.status != "ACTIVE":
                raise ValidationError("This account is inactive. Activate it first.")
            if txn_type == "WITHDRAWAL" and amount > account.current_balance:
                raise ValidationError(
                    f"Insufficient balance. Available balance is Rs. {account.current_balance}."
                )
            if txn_type == "DEPOSIT":
                account.current_balance += amount
            else:
                account.current_balance -= amount
            account.save(update_fields=["current_balance"])
            txn = Transaction.objects.create(
                account=account,
                transaction_type=txn_type,
                amount=amount,
                balance_after_transaction=account.current_balance,
            )
        self.current_balance = account.current_balance
        return txn

    def deposit(self, amount):
        return self._apply("DEPOSIT", amount)

    def withdraw(self, amount):
        return self._apply("WITHDRAWAL", amount)

    def save(self, *args, **kwargs):
        # A brand-new account starts with current balance = opening balance
        is_new = self._state.adding
        if is_new:
            self.current_balance = self.opening_balance
        super().save(*args, **kwargs)
        if is_new and self.opening_balance > 0:
            Transaction.objects.create(
                account=self,
                transaction_type="DEPOSIT",
                amount=self.opening_balance,
                balance_after_transaction=self.current_balance,
                remarks="Opening balance",
            )


class Transaction(models.Model):
    TYPES = [("DEPOSIT", "Deposit"), ("WITHDRAWAL", "Withdrawal")]

    transaction_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=10, choices=TYPES)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-transaction_date", "-transaction_id"]

    def __str__(self):
        return f"TXN{self.transaction_id:06d} {self.transaction_type} {self.amount}"
