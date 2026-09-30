from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import mixins, permissions, viewsets

from .forms import AccountCreateForm, AccountUpdateForm, CustomerForm, MoneyForm
from .models import BankAccount, Customer, Transaction
from .serializers import (
    BankAccountSerializer, CustomerSerializer, DepositSerializer,
    TransactionSerializer, WithdrawalSerializer,
)


def _paginate(request, queryset, per_page=10):
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@login_required
def dashboard(request):
    deposits = Transaction.objects.filter(transaction_type="DEPOSIT")
    withdrawals = Transaction.objects.filter(transaction_type="WITHDRAWAL")
    context = {
        "total_customers": Customer.objects.count(),
        "total_accounts": BankAccount.objects.count(),
        "active_accounts": BankAccount.objects.filter(status="ACTIVE").count(),
        "inactive_accounts": BankAccount.objects.filter(status="INACTIVE").count(),
        "total_deposits": deposits.aggregate(t=Sum("amount"))["t"] or 0,
        "total_withdrawals": withdrawals.aggregate(t=Sum("amount"))["t"] or 0,
        "recent_transactions": Transaction.objects.select_related("account__customer")[:6],
    }
    return render(request, "bank/dashboard.html", context)


# --------------------------------------------------------------------------
# Customers
# --------------------------------------------------------------------------
@login_required
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query) | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )
    return render(request, "bank/customer_list.html",
                  {"page_obj": _paginate(request, customers), "query": query})


@login_required
def customer_add(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        messages.success(request, f"Customer '{customer.full_name}' added successfully.")
        return redirect("customer_detail", pk=customer.pk)
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "bank/customer_form.html", {"form": form, "title": "Add New Customer"})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, "bank/customer_detail.html",
                  {"customer": customer, "accounts": customer.accounts.all()})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Customer information updated successfully.")
        return redirect("customer_detail", pk=pk)
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "bank/customer_form.html",
                  {"form": form, "title": "Update Customer", "customer": customer})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        name = customer.full_name
        customer.delete()
        messages.success(request, f"Customer '{name}' and all linked accounts were deleted.")
        return redirect("customer_list")
    return render(request, "bank/confirm_delete.html", {
        "object_label": f"customer {customer.full_name}",
        "warning": "All bank accounts and transactions of this customer will also be deleted.",
        "cancel_url": "customer_list",
    })


# --------------------------------------------------------------------------
# Accounts
# --------------------------------------------------------------------------
@login_required
def account_list(request):
    query = request.GET.get("q", "").strip()
    accounts = BankAccount.objects.select_related("customer")
    if query:
        accounts = accounts.filter(
            Q(account_number__icontains=query) | Q(customer__full_name__icontains=query)
        )
    return render(request, "bank/account_list.html",
                  {"page_obj": _paginate(request, accounts), "query": query})


@login_required
def account_create(request):
    initial = {}
    if request.GET.get("customer"):
        initial["customer"] = request.GET["customer"]
    form = AccountCreateForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        account = form.save()
        messages.success(request, f"Account {account.account_number} created successfully.")
        return redirect("account_detail", pk=account.pk)
    if request.method == "POST":
        messages.error(request, "Please correct the errors below.")
    return render(request, "bank/account_form.html", {"form": form, "title": "Create Bank Account"})


@login_required
def account_detail(request, pk):
    account = get_object_or_404(BankAccount.objects.select_related("customer"), pk=pk)
    return render(request, "bank/account_detail.html", {
        "account": account, "transactions": account.transactions.all()[:10],
    })


@login_required
def account_update(request, pk):
    account = get_object_or_404(BankAccount, pk=pk)
    form = AccountUpdateForm(request.POST or None, instance=account)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account information updated successfully.")
        return redirect("account_detail", pk=pk)
    return render(request, "bank/account_form.html",
                  {"form": form, "title": "Update Account", "account": account})


@login_required
def account_toggle_status(request, pk):
    account = get_object_or_404(BankAccount, pk=pk)
    if request.method == "POST":
        account.status = "INACTIVE" if account.is_active else "ACTIVE"
        account.save(update_fields=["status"])
        messages.success(request, f"Account {account.account_number} is now {account.get_status_display()}.")
    return redirect(request.POST.get("next") or "account_list")


@login_required
def account_delete(request, pk):
    account = get_object_or_404(BankAccount, pk=pk)
    if request.method == "POST":
        number = account.account_number
        account.delete()
        messages.success(request, f"Account {number} deleted successfully.")
        return redirect("account_list")
    return render(request, "bank/confirm_delete.html", {
        "object_label": f"account {account.account_number}",
        "warning": "All transactions of this account will also be deleted.",
        "cancel_url": "account_list",
    })


# --------------------------------------------------------------------------
# Deposit / Withdrawal
# --------------------------------------------------------------------------
def _money_view(request, kind):
    form = MoneyForm(request.POST or None, initial={"account": request.GET.get("account")})
    if request.method == "POST" and form.is_valid():
        account = form.cleaned_data["account"]
        amount = form.cleaned_data["amount"]
        try:
            txn = account.deposit(amount) if kind == "DEPOSIT" else account.withdraw(amount)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            word = "deposited into" if kind == "DEPOSIT" else "withdrawn from"
            messages.success(
                request,
                f"Rs. {txn.amount} {word} account {account.account_number}. "
                f"New balance: Rs. {txn.balance_after_transaction}.",
            )
            return redirect("deposit" if kind == "DEPOSIT" else "withdraw")
    history = Transaction.objects.filter(transaction_type=kind).select_related("account__customer")[:8]
    return render(request, "bank/money_form.html", {
        "form": form, "kind": kind, "history": history,
        "title": "Deposit Money" if kind == "DEPOSIT" else "Withdraw Money",
    })


@login_required
def deposit(request):
    return _money_view(request, "DEPOSIT")


@login_required
def withdraw(request):
    return _money_view(request, "WITHDRAWAL")


@login_required
def transaction_list(request):
    txns = Transaction.objects.select_related("account__customer")
    kind = request.GET.get("type", "")
    query = request.GET.get("q", "").strip()
    if kind in ("DEPOSIT", "WITHDRAWAL"):
        txns = txns.filter(transaction_type=kind)
    if query:
        txns = txns.filter(account__account_number__icontains=query)
    return render(request, "bank/transaction_list.html",
                  {"page_obj": _paginate(request, txns, 12), "kind": kind, "query": query})


@login_required
def api_docs(request):
    return render(request, "bank/api_docs.html")


# --------------------------------------------------------------------------
# REST API (Django REST Framework)
# --------------------------------------------------------------------------
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("customer_id")
    serializer_class = CustomerSerializer


class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.select_related("customer").order_by("created_at")
    serializer_class = BankAccountSerializer


class TransactionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """Ledger entries are read-only so history can never be edited."""
    queryset = Transaction.objects.select_related("account").order_by("transaction_id")
    serializer_class = TransactionSerializer


class DepositViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Transaction.objects.filter(transaction_type="DEPOSIT").order_by("transaction_id")

    def get_serializer_class(self):
        return DepositSerializer if self.action == "create" else TransactionSerializer


class WithdrawalViewSet(DepositViewSet):
    queryset = Transaction.objects.filter(transaction_type="WITHDRAWAL").order_by("transaction_id")

    def get_serializer_class(self):
        return WithdrawalSerializer if self.action == "create" else TransactionSerializer
