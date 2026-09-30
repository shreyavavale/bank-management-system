from django.contrib import admin

from .models import BankAccount, Customer, Transaction


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_id", "full_name", "phone", "email", "created_at")
    search_fields = ("full_name", "email", "phone")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("account_number", "customer", "account_type", "current_balance", "status")
    list_filter = ("account_type", "status")
    search_fields = ("account_number", "customer__full_name")
    readonly_fields = ("current_balance",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id", "account", "transaction_type", "amount",
        "balance_after_transaction", "transaction_date",
    )
    list_filter = ("transaction_type",)
    search_fields = ("account__account_number",)
