from decimal import Decimal

from django import forms

from .models import BankAccount, Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["full_name", "date_of_birth", "gender", "phone", "email", "address"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_full_name(self):
        name = self.cleaned_data["full_name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("Full name must have at least 3 characters.")
        return name


class AccountCreateForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ["customer", "account_type", "opening_balance"]

    def clean_opening_balance(self):
        balance = self.cleaned_data["opening_balance"]
        if balance < 0:
            raise forms.ValidationError("Opening balance cannot be negative.")
        return balance


class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ["account_type", "status"]


class MoneyForm(forms.Form):
    """Shared by the Deposit and Withdrawal screens."""

    account = forms.ModelChoiceField(
        queryset=BankAccount.objects.none(), empty_label="-- Select account --"
    )
    amount = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01", "placeholder": "0.00"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = BankAccount.objects.filter(
            status="ACTIVE"
        ).select_related("customer")
        self.fields["account"].label_from_instance = (
            lambda a: f"{a.account_number} - {a.customer.full_name} (Rs. {a.current_balance})"
        )
