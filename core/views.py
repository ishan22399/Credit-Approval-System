"""
API Views for core app.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Max
from datetime import datetime, timedelta

from .models import Customer, Loan
from .serializers import (
    CustomerSerializer,
    CustomerRegistrationSerializer,
    CheckEligibilitySerializer,
    CheckEligibilityResponseSerializer,
    CreateLoanSerializer,
    CreateLoanResponseSerializer,
    LoanDetailSerializer,
    LoanListSerializer,
)
from .utils import (
    calculate_emi,
    calculate_credit_score,
    check_eligibility as check_eligibility_util,
    round_to_nearest_lakh,
)


@api_view(['POST'])
def register(request):
    """
    Register a new customer.
    
    Calculates approved_limit = 36 * monthly_salary (rounded to nearest lakh)
    Auto-generates customer_id as max existing + 1
    """
    serializer = CustomerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        # Extract data
        first_name = serializer.validated_data['first_name']
        last_name = serializer.validated_data['last_name']
        phone_number = serializer.validated_data['phone_number']
        age = serializer.validated_data['age']
        monthly_salary = serializer.validated_data['monthly_salary']
        
        # Check if customer already exists
        if Customer.objects.filter(phone_number=phone_number).exists():
            return Response(
                {'error': 'Customer with this phone number already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-generate customer_id (max + 1)
        max_customer_id = Customer.objects.aggregate(Max('customer_id'))['customer_id__max'] or 0
        new_customer_id = max_customer_id + 1
        
        # Calculate approved limit: 36 * monthly_salary, rounded to nearest lakh
        approved_limit = round_to_nearest_lakh(36 * monthly_salary)
        
        # Create customer
        customer = Customer.objects.create(
            customer_id=new_customer_id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            age=age,
            monthly_salary=monthly_salary,
            approved_limit=approved_limit,
            current_debt=0
        )
        
        # Return response
        response_data = {
            'customer_id': customer.customer_id,
            'name': f"{customer.first_name} {customer.last_name}",
            'age': customer.age,
            'monthly_income': customer.monthly_salary,
            'approved_limit': customer.approved_limit,
            'phone_number': customer.phone_number,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    """
    Check loan eligibility based on credit score.
    
    Returns:
        - approval: bool
        - interest_rate: float (original)
        - corrected_interest_rate: float (based on credit rating)
        - monthly_installment: float (EMI)
    """
    serializer = CheckEligibilitySerializer(data=request.data)
    
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
        # Get customer
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check eligibility
        result = check_eligibility_util(customer, loan_amount, interest_rate, tenure)
        
        # Calculate EMI with corrected rate if needed
        if result['approval']:
            final_rate = interest_rate
        else:
            final_rate = result['corrected_interest_rate']
        
        emi = calculate_emi(loan_amount, final_rate, tenure)
        
        response_data = {
            'customer_id': customer_id,
            'approval': result['approval'],
            'interest_rate': interest_rate,
            'corrected_interest_rate': result['corrected_interest_rate'],
            'tenure': tenure,
            'monthly_installment': emi,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_loan(request):
    """
    Create a new loan after checking eligibility.
    
    Returns:
        - loan_id: int (or null if rejected)
        - loan_approved: bool
        - message: str
        - monthly_installment: float
    """
    serializer = CreateLoanSerializer(data=request.data)
    
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
        # Get customer
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check eligibility
        result = check_eligibility_util(customer, loan_amount, interest_rate, tenure)
        
        if result['approval']:
            # Use corrected rate if different
            final_rate = interest_rate if interest_rate > result['corrected_interest_rate'] else result['corrected_interest_rate']
            
            # Calculate EMI
            emi = calculate_emi(loan_amount, final_rate, tenure)
            
            # Auto-generate loan_id (max + 1)
            max_loan_id = Loan.objects.aggregate(Max('loan_id'))['loan_id__max'] or 0
            new_loan_id = max_loan_id + 1
            
            # Create loan
            loan = Loan.objects.create(
                loan_id=new_loan_id,
                customer=customer,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=final_rate,
                monthly_repayment=emi,
                emis_paid_on_time=0,
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=tenure*30)).date()
            )
            
            # Update customer current_debt
            customer.current_debt += loan_amount
            customer.save()
            
            response_data = {
                'loan_id': loan.loan_id,
                'customer_id': customer_id,
                'loan_approved': True,
                'message': 'Loan approved successfully.',
                'monthly_installment': emi,
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            emi = calculate_emi(loan_amount, result['corrected_interest_rate'], tenure)
            
            response_data = {
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': 'Loan request rejected.',
                'monthly_installment': emi,
            }
            
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def view_loan(request, loan_id):
    """
    View loan details along with customer information.
    """
    try:
        loan = Loan.objects.get(loan_id=loan_id)
    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = LoanDetailSerializer(loan)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def view_loans(request, customer_id):
    """
    View all loans of a customer with repayments_left calculated.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    loans = Loan.objects.filter(customer=customer)
    serializer = LoanListSerializer(loans, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)
