"""
Models for core app.
"""

from django.db import models
from django.utils import timezone

class Customer(models.Model):
    customer_id = models.IntegerField(primary_key=True)  # Changed from AutoField to IntegerField
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Allow null for imported data
    age = models.IntegerField()
    monthly_salary = models.FloatField()
    approved_limit = models.FloatField()
    current_debt = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['customer_id']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"


class Loan(models.Model):
    loan_id = models.IntegerField(primary_key=True)  # Changed from AutoField to IntegerField
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.FloatField()
    tenure = models.IntegerField()  # months
    interest_rate = models.FloatField()
    monthly_repayment = models.FloatField()
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'
        ordering = ['loan_id']

    def __str__(self):
        return f"Loan {self.loan_id} - Customer {self.customer.customer_id}"

    @property
    def repayments_left(self):
        return self.tenure - self.emis_paid_on_time
