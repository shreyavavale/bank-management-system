"""Fill the database with demo data:  python manage.py load_sample_data"""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from bank.models import BankAccount, Customer, Transaction

CUSTOMERS = [
    ("Aarav Sharma", date(1995, 4, 12), "M", "9876500001", "aarav.sharma@example.com", "12, MG Road, Pune"),
    ("Priya Deshmukh", date(1998, 9, 23), "F", "9876500002", "priya.deshmukh@example.com", "45, Shivaji Nagar, Pune"),
    ("Rohan Patil", date(1990, 1, 5), "M", "9876500003", "rohan.patil@example.com", "8, Kothrud, Pune"),
    ("Sneha Kulkarni", date(1993, 7, 18), "F", "9876500004", "sneha.kulkarni@example.com", "21, Aundh, Pune"),
    ("Vikram Joshi", date(1985, 11, 30), "M", "9876500005", "vikram.joshi@example.com", "3, Camp Area, Pune"),
    ("Anjali More", date(2000, 2, 14), "F", "9876500006", "anjali.more@example.com", "77, Baner, Pune"),
    ("Kunal Jadhav", date(1992, 6, 9), "M", "9876500007", "kunal.jadhav@example.com", "16, Hadapsar, Pune"),
    ("Meera Nair", date(1997, 12, 1), "F", "9876500008", "meera.nair@example.com", "5, Viman Nagar, Pune"),
]


class Command(BaseCommand):
    help = "Create demo admin user, customers, accounts and transactions"

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write("Admin user created  ->  admin / admin123")

        if Customer.objects.exists():
            self.stdout.write(self.style.WARNING("Sample data already present - skipping."))
            return

        types = ["SAVINGS", "CURRENT"]
        for i, (name, dob, gender, phone, email, addr) in enumerate(CUSTOMERS):
            customer = Customer.objects.create(
                full_name=name, date_of_birth=dob, gender=gender,
                phone=phone, email=email, address=addr,
            )
            account = BankAccount.objects.create(
                customer=customer, account_type=types[i % 2],
                opening_balance=Decimal(5000 + i * 2500),
            )
            account.deposit(Decimal("1500.00") + i * 250)
            account.withdraw(Decimal("800.00"))
            if i % 3 == 0:
                account.deposit(Decimal("3200.50"))

        # make one account inactive to demonstrate the status feature
        last = BankAccount.objects.order_by("created_at").last()
        last.status = "INACTIVE"
        last.save(update_fields=["status"])

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {Customer.objects.count()} customers, {BankAccount.objects.count()} accounts, "
            f"{Transaction.objects.count()} transactions."
        ))
