"""
Serializers for core app.
"""

from rest_framework import serializers
from .models import Customer, Loan


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Customer
        fields = [
            'customer_id',
            'first_name',
            'last_name',
            'name',
            'phone_number',
            'age',
            'monthly_salary',
            'approved_limit',
            'current_debt',
        ]
        read_only_fields = ['customer_id', 'approved_limit']


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'age',
            'monthly_salary',
        ]


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'customer',
            'loan_amount',
            'tenure',
            'interest_rate',
            'monthly_repayment',
            'emis_paid_on_time',
            'start_date',
            'end_date',
            'repayments_left',
        ]
        read_only_fields = ['loan_id', 'monthly_repayment', 'repayments_left']


class LoanDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'customer',
            'loan_amount',
            'tenure',
            'interest_rate',
            'monthly_repayment',
            'emis_paid_on_time',
            'start_date',
            'end_date',
            'repayments_left',
        ]

    def get_customer(self, obj):
        customer = obj.customer
        return {
            'customer_id': customer.customer_id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone_number': customer.phone_number,
            'age': customer.age,
            'monthly_salary': customer.monthly_salary,
            'approved_limit': customer.approved_limit,
            'current_debt': customer.current_debt,
        }


class LoanListSerializer(serializers.ModelSerializer):
    customer_id = serializers.SerializerMethodField()
    repayments_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'customer_id',
            'loan_amount',
            'tenure',
            'interest_rate',
            'monthly_repayment',
            'emis_paid_on_time',
            'start_date',
            'end_date',
            'repayments_left',
        ]

    def get_customer_id(self, obj):
        return obj.customer.customer_id


class CheckEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()


class CheckEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()


class CreateLoanSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()


class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField()
