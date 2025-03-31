from django.db import models
import random
from django.utils import timezone
from decimal import Decimal

class Account(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    account_number = models.CharField(max_length=14, unique=True, blank=True, editable=True)  # Custom primary key
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    photo = models.ImageField(upload_to='photos/')
    date = models.DateField()
    terms_accepted = models.BooleanField(default=False)
    generated_number = models.CharField(max_length=12, null=True, blank=True)
    pin = models.CharField(max_length=6, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = f"082322{''.join([str(random.randint(0, 9)) for _ in range(8)])}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fname} {self.lname}"

class Transaction(models.Model):
    account_number = models.CharField(max_length=14)  # Store the account_number directly
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Transaction {self.pk} for account {self.account_number}"

    class Meta:
        ordering = ['-date']

class Loan(models.Model):
    account_number = models.CharField(max_length=14)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.PositiveIntegerField(help_text="")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField(default=timezone.now, editable=False)
    end_date = models.DateField(null=True, blank=True, editable=False)
    payed_loan = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remaining_loan = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    reason = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.tenure * 30)
        self.remaining_loan = self.loan_amount - self.payed_loan
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Loan {self.pk} for account {self.account_number}"

    def __str__(self):
        return f"Loan {self.pk} for account {self.account_number}"

    class Meta:
        unique_together = ('account_number', 'reason')

class LoanTransaction(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=14, editable=False)
    total_loan = models.DecimalField(max_digits=10, decimal_places=2)
    payed_loan = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    remaining_loan = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Populate fields from the related Loan instance
        if self.loan:
            self.account_number = self.loan.account_number
            self.total_loan = self.loan.loan_amount  # Make sure to set total_loan
            self.remaining_loan = self.loan.remaining_loan
            self.payed_loan = self.loan.payed_loan
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transaction {self.pk} for loan {self.loan.pk}"

class FixedDeposit(models.Model):
    account_number = models.CharField(max_length=14)
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual interest rate
    start_date = models.DateField(default=timezone.now)
    maturity_date = models.DateField()
    matured_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def calculate_matured_amount(self):
        # Calculate the number of years between start_date and maturity_date
        delta = self.maturity_date - self.start_date
        years = Decimal(delta.days) / Decimal(365.25)
        
        # Formula for compound interest
        interest_rate_decimal = Decimal(self.interest_rate) / Decimal(100)
        matured_amount = self.principal_amount * ((1 + interest_rate_decimal) ** years)
        return matured_amount

    def save(self, *args, **kwargs):
        # Calculate matured amount before saving
        if not self.matured_amount:
            self.matured_amount = self.calculate_matured_amount()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"FD {self.pk} for account {self.account_number}"
