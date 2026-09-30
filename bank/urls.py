from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("customers", views.CustomerViewSet, basename="api-customer")
router.register("accounts", views.BankAccountViewSet, basename="api-account")
router.register("deposits", views.DepositViewSet, basename="api-deposit")
router.register("withdrawals", views.WithdrawalViewSet, basename="api-withdrawal")
router.register("transactions", views.TransactionViewSet, basename="api-transaction")

urlpatterns = [
    # Authentication
    path("login/", auth_views.LoginView.as_view(template_name="bank/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Customers
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/add/", views.customer_add, name="customer_add"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_update, name="customer_update"),
    path("customers/<int:pk>/delete/", views.customer_delete, name="customer_delete"),

    # Accounts
    path("accounts/", views.account_list, name="account_list"),
    path("accounts/create/", views.account_create, name="account_create"),
    path("accounts/<str:pk>/", views.account_detail, name="account_detail"),
    path("accounts/<str:pk>/edit/", views.account_update, name="account_update"),
    path("accounts/<str:pk>/toggle/", views.account_toggle_status, name="account_toggle"),
    path("accounts/<str:pk>/delete/", views.account_delete, name="account_delete"),

    # Money operations
    path("deposit/", views.deposit, name="deposit"),
    path("withdraw/", views.withdraw, name="withdraw"),
    path("transactions/", views.transaction_list, name="transaction_list"),

    # REST API
    path("api-docs/", views.api_docs, name="api_docs"),
    path("api/", include(router.urls)),
]
