"""
Django admin interface for managing customers and loans
"""

from django.contrib import admin
from .models import Customer, Loan


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # what fields to show in the list view
    list_display = ('customer_id', 'first_name', 'last_name', 'phone_number', 'monthly_salary', 'approved_limit', 'current_debt')
    list_filter = ('created_at',)
    search_fields = ('first_name', 'last_name', 'phone_number')
    ordering = ('customer_id',)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'customer', 'loan_amount', 'tenure', 'interest_rate', 'monthly_repayment', 'start_date')
    list_filter = ('start_date', 'created_at')
    search_fields = ('customer__first_name', 'customer__last_name', 'loan_id')
    ordering = ('loan_id',)
