"""
Credit scoring and EMI calculation utilities.
"""

from datetime import datetime, timedelta
from .models import Loan
from django.db.models import Sum, Count, Q


def calculate_emi(principal, monthly_rate, tenure_months):
    # compound interest formula:
    # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    # basically: loan amount * monthly rate / number of months with interest
    if monthly_rate == 0:
        return principal / tenure_months
    
    r = monthly_rate / 100 / 12
    n = tenure_months
    
    if r == 0:
        return principal / n
    
    numerator = r * ((1 + r) ** n)
    denominator = ((1 + r) ** n) - 1
    
    emi = principal * (numerator / denominator)
    return round(emi, 2)


def calculate_credit_score(customer):
    # your score is 0-100 based on:
    # 1. did you pay EMIs on time (30%)
    # 2. how many loans you took (20%)
    # 3. did you take loans this year (20%)
    # 4. total money you borrowed (30%)
    # if you owe more than your limit, score = 0
    
    # Check if current debt exceeds approved limit
    if customer.current_debt > customer.approved_limit:
        return 0
    
    # Get all loans for customer
    all_loans = Loan.objects.filter(customer=customer)
    
    if not all_loans.exists():
        # New customer - give base score (51 to pass > 50 threshold)
        return 51
    
    score = 0
    
    # 1. Past loans paid on time (30 points max)
    total_loans = all_loans.count()
    if total_loans > 0:
        on_time_loans = all_loans.filter(emis_paid_on_time__gte=1).count()
        on_time_ratio = on_time_loans / total_loans
        score += on_time_ratio * 30
    
    # 2. Number of loans taken (20 points max)
    # More loans = more experience
    loan_count_score = min(total_loans / 5, 1.0) * 20  # Max at 5+ loans
    score += loan_count_score
    
    # 3. Loan activity in current year (20 points max)
    current_year = datetime.now().year
    current_year_loans = all_loans.filter(start_date__year=current_year).count()
    recent_activity_score = min(current_year_loans / 3, 1.0) * 20  # Max at 3+ loans in year
    score += recent_activity_score
    
    # 4. Loan approved volume (30 points max)
    total_volume = all_loans.aggregate(Sum('loan_amount'))['loan_amount__sum'] or 0
    salary_years = customer.monthly_salary * 12
    volume_ratio = total_volume / (salary_years * 2) if salary_years > 0 else 0
    volume_score = min(volume_ratio, 1.0) * 30
    score += volume_score
    
    return min(round(score, 2), 100)


def check_eligibility(customer, loan_amount, interest_rate, tenure):
    """
    Check loan eligibility based on credit score and other factors.
    
    Returns:
        dict with approval status and corrected interest rate
    """
    # Calculate credit score
    credit_score = calculate_credit_score(customer)
    
    # Calculate monthly EMI
    emi = calculate_emi(loan_amount, interest_rate, tenure)
    
    # Calculate sum of current EMIs
    current_loans = Loan.objects.filter(customer=customer)
    total_current_emi = current_loans.aggregate(Sum('monthly_repayment'))['monthly_repayment__sum'] or 0
    total_emi_with_new = total_current_emi + emi
    
    # Decision logic
    approval = False
    corrected_rate = interest_rate
    
    # Rule 1: If current debt > approved limit, reject
    if customer.current_debt > customer.approved_limit:
        approval = False
        corrected_rate = interest_rate
    # Rule 2: If sum of EMIs > 50% salary, reject
    elif total_emi_with_new > (customer.monthly_salary * 0.5):
        approval = False
        corrected_rate = interest_rate
    # Rule 3: Credit score based approval
    elif credit_score > 50:
        approval = True
    elif 30 < credit_score <= 50:
        # Approve only if rate > 12%
        if interest_rate > 12:
            approval = True
        else:
            approval = False
            corrected_rate = 12.0
    elif 10 < credit_score <= 30:
        # Approve only if rate > 16%
        if interest_rate > 16:
            approval = True
        else:
            approval = False
            corrected_rate = 16.0
    else:  # credit_score <= 10
        approval = False
        corrected_rate = interest_rate
    
    return {
        'approval': approval,
        'corrected_interest_rate': corrected_rate,
        'monthly_installment': emi,
        'credit_score': credit_score,
    }


def round_to_nearest_lakh(amount):
    """
    Round amount to nearest lakh (100,000).
    """
    return round(amount / 100000) * 100000
